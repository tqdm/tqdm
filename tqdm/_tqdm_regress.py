"""
Progress bar with machine learning (linear/polynomial regression) to better predict time!
Includes a default (x)range iterator printing to stderr.

Usage:
  >>> from tqdm_regress import tsrange[, tqdm_regressl]
  >>> for i in tsrange(10): #same as: for i in tqdm_regress(xrange(10))
  ...     ...
"""
# future division is important to divide integers and get as
# a result precise floating numbers (instead of truncated int)
from __future__ import division, absolute_import
# import utilities
import random
import sys
from copy import deepcopy
from math import log, exp, sqrt
# import compatibility functions
from ._utils import _range
# to inherit from the tqdm class
from ._tqdm import tqdm


__author__ = {"github.com/": ["lrq3000"]}
__all__ = ['tqdm_regress', 'tsrange']


def in_notebook():
    """
    Returns True if the module is running under IPython notebook,
    False otherwise (IPython shell or other Python shell).
    """
    return 'ipykernel' in sys.modules


class TPlot(object):
    """
    Dynamical real-time updating plot
    NOTE: execute before `%matplotlib inline` in IPython notebook
    """
    def __init__(self, fid=0, norefresh=False, title=None, xlabel=None, ylabel=None, nolegend=False):
        # Import matplotlib
        try:
            import matplotlib.pyplot as plt
            self.plt = plt
        except ImportError:
            raise ImportError('matplotlib is necessary for plotting!')

        # Interactive mode (important for dynamic update)
        self.plt.ion()
        # Create a new figure
        fig=self.plt.figure(fid)
        #plt.axis([0,20,0,20]) # will be automagically rescaled
        # Save arguments
        self.fid = fid
        self.norefresh = norefresh
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.nolegend = nolegend
        # Special refresh function for notebook
        self.in_notebook = False
        if in_notebook():
            from IPython import display
            self.display = display
            self.in_notebook = True

    def add(self, x, y, *args, **kwargs):
        """Add one point to the figure
        or redraw whole figure if list of points"""
        self.plt.figure(self.fid)
        self.plt.plot(x, y, *args, **kwargs)
        if not self.norefresh:
            self.refresh()

    def refresh(self):
        """Refresh plot display"""
        # Select figure
        self.plt.figure(self.fid)
        # Redraw title and axes
        if self.title:
            self.plt.title(self.title)
        if self.xlabel:
            self.plt.xlabel(self.xlabel)
        if self.ylabel:
            self.plt.ylabel(self.ylabel)
        # Redraw legend
        if not self.nolegend:  # avoid userwarning: no labelled objects found...
            self.plt.legend(loc='best')
        # Realtime updating for IPython jupyter
        # Need to %matplotlib inline
        if self.in_notebook:
            self.display.clear_output(wait=True)  # wait=True allows to refresh inline
            self.display.display(self.plt.gcf())
        else:
            # Refresh display
            self.plt.gcf()
        # Pause to allow the graphics redraw to complete (important)
        self.plt.pause(0.0001)  # raises a deprecationwarning about using default loop..

    def clear(self):
        """Clear the whole plot (points, axes, legend, title, etc)"""
        self.plt.figure(self.fid)
        self.plt.clf()


class RegressionPoly(object):
    """Multivariable linear/polynomial/ridge regression in pure Python"""
    def __init__(self, total, order=2.5, batch_size=10, proba_add_batch=0.5):
        self.total = total
        self.order = order
        self.batch_size = batch_size
        self.batch_pts = []
        self.proba_add_batch = proba_add_batch
        self.params = []
        self.plots = None
        self.last_cost = None
        self.cost_history = []
        self.last_it = 0

        # feature scale total
        self.total_poly = self.polynomize(self.total, self.order)
        # init parameters
        self.params = [random.random() for _ in range(len(self.total_poly)+1)]  # +1 for bias unit

    def add_sample(self, x, y, iteration=0, random_insert=True):
        self.last_it = iteration
        add_point = False
        # Add current point to mini-batch
        if len(self.batch_pts) < self.batch_size:
            # Below batch size, we can add
            add_point = True
        else:
            if random_insert:
                # Above batch size, randomly add or not a point
                # The goal is to keep a batch spanning a longer timeframe than just last points
                # in order to avoid forgetting of past
                if random.random() <= self.proba_add_batch:
                    self.batch_pts.pop(random.randrange(0, self.batch_size))
                    add_point = True
            else:
                # Above batch size, remove oldest point and add new point
                # We get a moving window over the last seen points
                self.batch_pts.pop(0)
                add_point = True

        if add_point:
            # polynomize (add more features and make non-linear, polynomial regression)
            x_poly = self.polynomize(x, self.order)
            # feature scaling
            x_poly = self.feature_scaling(x_poly, self.total_poly)
            # add bias unit
            x_poly = self.add_bias_unit(x_poly)
            # add preprocessed point to batch
            self.batch_pts.append([x_poly, y, iteration])
            return True
        else:
            return False

    def fit(self, rate=0.5, lamb=0.0, rate_decay=0.0, relu=True, iteration=0, **kwargs):
        # Extract separately x and y
        x_batch, y_batch, real_it_batch = zip(*self.batch_pts)

        # Compute gradient and cost!
        grad, self.last_cost = self.minibatch_gradient_descent(x_batch, y_batch,
                                                self.params, rate=rate,
                                                lamb=lamb,
                                                rate_decay=rate_decay,
                                                it=iteration, relu=relu,
                                               **kwargs)

        # Update parameters: params = params - grad
        self.params = [pi - gi for pi, gi in zip(self.params, grad)]

    def _predict(self, x, params):
        """(Internal) Predict y using learnt model"""
        return self._dot_product(x, params)

    def predict(self, x):
        """Preprocess x and predict y"""
        return self._predict(self._preprocess(x), self.params)

    def _preprocess(self, x):
        """Preprocess a raw sample x"""
        x_poly = self.polynomize(x, self.order)
        x_poly = self.add_bias_unit(self.feature_scaling(x_poly, self.total_poly))
        return x_poly

    def plot(self, iteration=None, plot_avg_every=10):
        """Plot convergence error and decision frontier"""
        # Init plots if not yet created
        if self.plots is None:
            self.plots = [TPlot(1, title='Cost convergence',
                                xlabel='iteration', ylabel='error avg', nolegend=True),
                          TPlot(2, title='Decision frontier',
                               xlabel='x (iteration)', ylabel='y (cumulative time)')]
        tp1, tp2 = self.plots

        # Add last computed cost to history
        if self.last_cost is not None:
            self.cost_history.append(self.last_cost)

        # Plot if enough history
        if len(self.cost_history) >= plot_avg_every or iteration is None:
            # Plot convergence error
            if iteration:
                if plot_avg_every > 1:
                    # Plot by smoothing over several points
                    tp1.add(iteration, sum(self.cost_history) / len(self.cost_history), 'xb')
                else:
                    # Plot every points
                    tp1.add(iteration, self.last_cost, 'xb')
                # clear up last points plotted
                self.cost_history = []

            # Plot decision frontier/boundary
            # sort before to plot a nice continuous line
            # x[0][1] is the real value of x (x[0] = x_poly)
            # (and x[0][0] = bias unit)
            batch_pts_sorted = sorted(self.batch_pts, key=lambda x: x[0][1])
            # Unpack batch
            x_batch, y_batch, real_it_batch = zip(*batch_pts_sorted)
            # Denormalize to get original X values
            x_batch_unnorm = [(xi[1]+0.5)*self.total for xi in x_batch]
            # Clear up previous frontier
            tp2.clear()
            # Plot frontier
            tp2.add(x_batch_unnorm, [self._predict(x, self.params) for x in x_batch], 'r-', label='ypred (predicted time)')
            # Plot last seen points
            tp2.add(x_batch_unnorm, y_batch, 'xb', label='y (time)')

    @staticmethod
    def _dot_product(a, b):
        """Dot product of two vectors (lists)"""
        # sum(a*b)
        return sum(x*y for x,y in zip(a,b))

    @staticmethod
    def add_bias_unit(x):
        """Add bias unit"""
        return [1] + x # prepend bias unit

    @staticmethod
    def feature_scaling(x_poly, total_poly, meannorm=True):
        """Apply feature scaling (bound to [0.0, 1.0]) + optional mean normalization [-0.5, 0.5]
        Note: always do scaling after polynomize, not before."""
        #return (x-(total/2)) / total
        # (x/total) - 0.5
        if meannorm:
            m = 0.5
        else:
            # Avoid mean normalization if using relu (because else we'll get negative values)
            m = 0.0
        return [(xi / ti) - m for xi, ti in zip(x_poly, total_poly)]

    @staticmethod
    def flat_spot_fix(grad):
        """Add small constant to avoid gradient getting stuck"""
        # constant = sum([g**2 for g in grad])**0.5 / len(grad)
        #return [g+constant for g in grad]
        return [g + g/1000 for g in grad]

    @staticmethod
    def polynomize(x, order=2.5):
        """Compute polynomials from a single value
        If order = z.5 (z + 1/2) then sqrt, log and exp will be added.
        Note: should polynomize always before feature scaling."""
        if not isinstance(x, list):
            x = [x]
        x_poly = deepcopy(x)  # copy the list
        if order > 1.0:
            # special funcs: sqrt, log and exp
            if order - int(order) > 0.0:
                for xi in x:
                    try:
                        x_poly.extend([xi**0.5, log(xi), exp(xi)])
                    except ValueError:  # log(0.0) is undefined
                        x_poly.extend([0.0, 0.0, 0.0])
            # Higher order polynomials (starting from x^2)
            for o in _range(2, int(order)+1):  # start from x^2
                x_poly.extend([xi**o for xi in x])
        return x_poly

    def stochastic_gradient_descent(self, x, y, params, rate=0.7, lamb=0.01, relu=False, rate_decay=0.0, it=0):
        """Stochastic gradient descent (one point at a time)"""
        if rate_decay and it > 0:
            rate = rate / (1 + (it - 1) * rate_decay)
        if relu:
            params = [max(0, param) for param in params]
        pred_y = self._predict(x_bias, params)
        # (pred_y - y)
        cost_grad = pred_y - y
        # rate * x * cost_grad
        grad = [rate * xi * cost_grad for xi in x_bias]
        grad = self.flat_spot_fix(grad)
        if lamb > 0:
            # lambda/m * params
            complexity_cost = [lamb * param for param in params]
            grad = [grad[0]] + [g+c for g,c in zip(grad[1:], complexity_cost[1:])]
        # 1/2 * cost_grad^2
        cost = 0.5 * cost_grad**2
        return grad, cost

    def minibatch_gradient_descent(self, x_batch, y_batch, params, rate=0.7, lamb=0.01, relu=False, rate_decay=0.0, it=0):
        """Minibatch gradient descent (with several points as a list of points)"""
        if rate_decay and it > 0:
            rate = rate / (1 + (it - 1) * rate_decay)
        if relu:
            params = [max(0, param) for param in params]
        pred_y = [self._predict(x_poly, params) for x_poly in x_batch]
        # (pred_y - y)
        cost_grad = [py - y for py, y in zip(pred_y, y_batch)]
        # rate * 1/m * sum(x_im * cost_grad_m)
        grad = [rate * 1.0/len(x_batch) * sum(x_im * c_m for x_im, c_m in zip(x_i, cost_grad)) for x_i in zip(*x_batch)]
        grad = self.flat_spot_fix(grad)
        if lamb > 0:
            # lambda/m * params
            complexity_cost = [lamb * param for param in params]
            # Do not regularize theta0 param (the bias unit), else horrible result
            grad = [grad[0]] + [g+c for g,c in zip(grad[1:], complexity_cost[1:])]
        # 1/2 * sum(cost_grad^2)
        cost = 1.0/(2*len(x_batch)) * sum(c_m**2 for c_m in cost_grad)
        return grad, cost

    def _compute_least_square_errors(self, x_batch, y_batch, params):
        """Compute error for a list of points and return list"""
        return [((self._predict(x, params) - y)**2)**0.5 for x,y in zip(x_batch, y_batch)]
    
    def compute_least_square_error(self, x_batch=None, y_batch=None):
        """Compute sum of errors for a list of points and return scalar"""
        if x_batch is None or y_batch is None:
            x_batch, y_batch, _ = zip(*self.batch_pts)
        return sum(self._compute_least_square_errors(x_batch, y_batch, self.params)) / (2*len(x_batch))

    def check_error(self, x_batch, y_batch, total, threshold=0.0001):
        """Check if error is below a threshold for a list of points"""
        err = self._compute_least_square_errors(x_batch, y_batch, total, self.params)
        return all([e < 0.0001 for e in err])

    @staticmethod
    def randomly(seq):
        """Walk randomly through a list of points (enhance SGD learning)"""
        import random
        shuffled = list(seq)
        random.shuffle(shuffled)
        return iter(shuffled)


class RegressionNormalEq(RegressionPoly):
    """Analytical polynomial regression using the Normal Equation in Numpy"""
    # Note that it is not possible in pure python nor by numpy except lstsq because
    # of a catastrophic loss of precision, see http://stackoverflow.com/a/30856590/1121352
    # Or can try to use fractions or Pyla (Python Linear Algebra, pure python)

    def __init__(self, *args, **kwargs):
        import numpy as np
        self.np = np
        super(RegressionNormalEq, self).__init__(*args, **kwargs)

    def add_sample(self, x, y, iteration=0, random_insert=False):
        super(RegressionNormalEq, self).add_sample(x, y, iteration, random_insert)

    def fit(self):
        x_only, y_only, it = zip(*self.batch_pts)

        # Convert to numpy datastructs to pass to numpy func
        # Not necessary but more efficient (batch processing)
        x_batch = self.np.mat(x_only)
        y_batch = self.np.array(y_only)

        # Compute cost before (to avoid tampering)
        self.last_cost = self.compute_least_square_error(x_batch, y_batch)

        # Regress analytically! Beware, cubic complexity so can be slow if number of features huge
        self.params = self.np.linalg.lstsq(x_batch, y_batch)[0]

    @staticmethod
    def _dot_product(a, b):
        """Dot product of two vectors or matrices"""
        # sum(a*b)
        return self.np.dot(a, b)

    def _predict(self, x, params):
        return self.np.dot(x, params)

    def add_bias_unit(self, x):
        try:
            # x is a matrix of several samples, use optimized trick
            return self.np.c_[self.np.ones(x.shape[0]), x]
        except AttributeError:
            # else single sample (simple list), call parent
            return super(RegressionNormalEq, self).add_bias_unit(x)

    def _compute_least_square_errors(self, x_batch, y_batch, params):
        """Compute error for a list of points and return list"""
        return self.np.power(self.np.power(self._predict(x_batch, params) - y_batch, 2), 0.5)

    def compute_least_square_error(self, x_batch=None, y_batch=None):
        """Compute sum of errors for a list of points and return scalar"""
        if x_batch is None or y_batch is None:
            x_batch, y_batch, _ = zip(*self.batch_pts)
        return self.np.sum(self._compute_least_square_errors(x_batch, y_batch, self.params)) / (2*len(x_batch))


class RegressionSklearn(RegressionNormalEq):
    """Scikit-learn regression"""

    def __init__(self, total, order=2.5, batch_size=10, proba_add_batch=0.5, regressor='PassiveAggressive', **kwargs):
        import numpy as np
        import sklearn as sk
        from sklearn import linear_model
        self.np = np

        # Load exceptions
        try:  # sklearn v0.18
            self.notfiterr = sk.exceptions.NotFittedError
        except AttributeError:  # sklearn v0.17
            self.notfiterr = sk.utils.validation.NotFittedError

        # Initialize model
        if regressor.lower() == 'passiveaggressive':
            self.model = linear_model.PassiveAggressiveRegressor(**kwargs)
        else:
            self.model = linear_model.SGDRegressor(eta0=1, **kwargs)

        super(RegressionSklearn, self).__init__(total, order, batch_size, proba_add_batch)

    def add_sample(self, x, y, iteration=0, random_insert=True):
        super(RegressionSklearn, self).add_sample(x, y, iteration, random_insert)

    def fit(self, *args, **kwargs):
        x_only, y_only, it = zip(*self.batch_pts)

        # Convert to numpy datastructs to pass to sklearn
        # Not necessary but more efficient (batch processing)
        x_batch = self.np.mat(x_only)
        y_batch = self.np.array(y_only)

        # Compute cost before (to avoid tampering)
        try:
            self.last_cost = self.compute_least_square_error(x_batch, y_batch)
        except self.notfiterr:
            # Not yet fitted, cannot compute error
            self.last_cost = None

        # Regress using partial fit
        self.model.partial_fit(x_batch, y_batch, *args, **kwargs)

    def _predict(self, x, params):
        x = self.np.mat(x)  # Ensure x is a matrix (else sklearn deprecation)
        return self.model.predict(x)


class tqdm_regress(tqdm):
    """
    Experimental IPython/Jupyter Notebook widget using tqdm!
    """

    # not a static method anymore
    def format_meter(self, n, total, elapsed, ncols=None, prefix='',
                     ascii=False, unit='it', unit_scale=False, rate=None,
                     bar_format=None):

        # Add new point and fit
        # But only if new iteration (else can be called by __repr__() and refresh())
        if n > self.model.last_it:
            # Add point (n, elapsed)
            self.model.add_sample([n], elapsed, n)
            # Fit (learn/train)
            # We do in a loop because to avoid the need to manually adjust learning rate
            for _ in _range(self.repeat):
                self.model.fit(**self.fit_params)
            # Plot if required
            if self.plot:
                self.model.plot(n)

            # Compute rate and ending time
            if n > 0 and total:
                # Predict ending time
                predicted_endtime = float(self.model.predict([total]))
                # Predicted endtime must be greater than current time else fitting failed!
                if predicted_endtime > 0 and predicted_endtime >= elapsed:
                    # Pessimistic: predict rate against remaining time, not total time
                    rate = (total - n) / (predicted_endtime - elapsed)

        # Do the rest as usual, with the provided rate computed by polynomial regression
        return super(tqdm_regress, self).format_meter(n, total, elapsed, ncols, prefix,
                     ascii, unit, unit_scale, rate,
                     bar_format)

    def __init__(self, iterable=None, algo='numpy', order=3, batch_size=50, proba_add_batch=0.5, repeat=10, plot=False, fit_params=None, **kwargs):
        """
        Parameters
        ----------
        iterable  : iterable, optional
            Iterable to decorate with a progressbar.
            Leave blank to manually manage the updates.
        algo  : str, optional
            Regression algorithm: 'descent', 'numpy', 'sklearn'
            Descent requires nothing, it's pure python.
            [default: 'numpy']
        order  : float, optional
            Highest order polynome to fit the time function.
            Can set z + 1/2 (eg, 3.5) to get log, exp and sqrt.
            [default: 3]
        batch_size  : int, optional
            Number of samples to memorize to fit model.
            [default: 50]
        proba_add_batch  : float, optional
            Probability to add a new sample to the memorized batch.
            [default: 0.5]
        repeat  : int, optional
            Number of time to repeat fitting for each new sample.
            Useless for algo='numpy'.
            [default: 10]
        plot  : bool, optional
            Display a realtime plots to check model's fitting.
        fit_params  : dict, optional
            Additional fit parameters.
        **kwargs: see other arguments for tqdm().

        Returns
        -------
        out  : decorated iterator.
        """
        total = kwargs.get('total', None)
        # Preprocess the arguments
        if total is None and iterable is not None:
            try:
                total = len(iterable)
            except (TypeError, AttributeError):
                total = None

        self.algo = algo
        self.plot = plot
        self.model = float
        self.repeat = repeat
        if fit_params is None:
            fit_params = {}
        self.fit_params = fit_params
        if algo == 'numpy':
            self.model = RegressionNormalEq(total, order, batch_size)
            self.repeat = 1  # useless to repeat with analytical solution
        elif algo == 'sklearn':
            self.model = RegressionSklearn(total, order, batch_size)
        else:
            self.model = RegressionPoly(total, order, batch_size, proba_add_batch)

        super(tqdm_regress, self).__init__(iterable, **kwargs)


def tsrange(*args, **kwargs):
    """
    A shortcut for tqdm_regress(xrange(*args), **kwargs).
    On Python3+ range is used instead of xrange.
    """
    return tqdm_regress(_range(*args), **kwargs)
