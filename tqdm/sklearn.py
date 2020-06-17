__author__ = {'github.com/': ['TurretAA12']}

@classmethod
def sklearn(tclass, *targs, **tkwargs):
    """
    Registers the given `tqdm` class with:
    sklearn.model_selection.
    ( cross_val_predict,
    | cross_val_score,
    | cross_validate,
    | learning_curve,
    | permutation_test_score,
    | validation_curve,
    | GridSearchCV,
    | RandomizedSearchCV
    )
    Parameters
    ----------
    targs, twargs : arguments for the tqdm instance

    For functions in model_selection, such as cross_val_predict,
    a tqdm version of the function is registered with sklearn.
    The tqdm function can be accessed by adding the letter 'p' to
    the beginning of name of the function.  For example, the tqdm
    version of 'cross_val_predict' would be accessed as 'pcross_val_predict'
    The tqdm functions also have one other alias which is accessed
    similarly to the tqdm pandas methods; by adding 'progress_' to the
    beginning of the function name. For example, the tqdm version of
    'cross_val_predict' can also be accessed as 'progress_cross_val_predict'.

    Example 1
    ---------
    >>> from sklearn import model_selection, datasets, neighbors
    >>> from tqdm import tqdm
    >>> mnist = datasets.fetch_openml('mnist_784', version=1)
    >>> X, y = mnist['data'], mnist['target']
    >>> # Register tqdm with sklearn by calling the `tqdm.sklearn` function
    >>> tqdm.sklearn(unit='cv')
    >>> basic_KNN = neighbors.KNeighborsClassifier()
    >>> # Using the tqdm version of the `cross_val_predict` function
    >>> model_selection.pcross_val_predict(basic_KNN, X[:5000], y[:5000], cv=10)
    >>> # or this -> model_selection.progress_cross_val_predict(...)

    When using a class from model_selection, such as GridSearchCV,
    a tqdm version of the fit method can be accessed. Access the tqdm
    version by calling `progress_fit`.

    Example 2
    ---------
    >>> from sklearn import model_selection, datasets, neighbors
    >>> from tqdm import tqdm
    >>> mnist = datasets.fetch_openml('mnist_784', version=1)
    >>> X, y = mnist['data'], mnist['target']
    >>> # Register tqdm with sklearn by calling `tqdm.sklearn` function
    >>> tqdm.sklearn()
    >>> basic_KNN = neighbors.KNeighborsClassifier()
    >>> params = {'n_neighbors': range(1, 11)}
    >>> search = model_selection.GridSearchCV(basic_KNN, params)
    >>> # Using the tqdm version of the `fit` method
    >>> search.progress_fit(X[:5000], y[:5000])

    **When using tqdm with sklearn it is highly recommended that you
    DO NOT use the verbose keyword argument. It may cause display
    issues with the tqdm progress bar.**
    """

    import types
    import functools
    import warnings
    import sklearn, sklearn.model_selection as model_selection

    earliest_supported_version = (0, 22, 1)
    if tuple(map(int, sklearn.__version__.split('.'))) < earliest_supported_version:
        warnings.warn("tqdm.sklearn() has not been tested on versions of sklearn earlier than {}".format(".".join(map(str, earliest_supported_version))), category=RuntimeWarning, stacklevel=2)

    # Maintainers do not forget to look at the default value of cv it may change over time and has changed in the past
    def progress_cross_val(option, estimator, X, *args, **kwargs):
        cv = kwargs['cv'] if 'cv' in kwargs else 5
        valid_options = ['predict', 'score', 'validate',
                        'learning_curve', 'permutation_test_score',
                        'validation_curve', 'SearchCV']

        if isinstance(option, (model_selection.GridSearchCV, model_selection.RandomizedSearchCV)):
            self = option
            estimator = self.estimator
            option = 'SearchCV'
        if ('verbose' in kwargs and kwargs['verbose'] >= 1) or ('self' in locals() and self.verbose >= 1):
            warnings.warn('Using verbose with tqdm can cause display issues with tqdm and/or the verbose messages', category=RuntimeWarning, stacklevel=2)

        assert option in valid_options, "[tqdm: Internal] progress_cross_val() {} not in valid options".format(option)

        option, validate = ('score', True) if option == 'validate' else (option, False)
        option, learning_curve = ('score', True) if option == 'learning_curve' else (option, False)
        option, permutation_test_score = ('score', True) if option == 'permutation_test_score' else (option, False)
        option, validation_curve = ('score', True) if option == 'validation_curve' else (option, False)
        option, SearchCV = ('score', True) if option == 'SearchCV' else (option, False)

        # TODO: parsing cv has NOT been tested with values other than ints. Need to test!
        if SearchCV:
            cv = self.cv
        if hasattr(cv, 'n_splits'):
            parsed_cv = cv.n_splits
        elif hasattr(cv, '__iter__') or isinstance(cv, types.GeneratorType):
            parsed_cv = len(list(cv))
        else:
            parsed_cv = cv if not SearchCV else 5

        if 'total' in kwargs:
            # Maybe remove this? IDK
            total = twargs['total']
        elif learning_curve:
            total = len(kwargs['train_sizes']) if 'train_sizes' in kwargs else 5
            total *= parsed_cv * 2 # The extra two is required because the `learning_curve` function trains on both training set and testing sets
        elif permutation_test_score:
            total = kwargs['n_permutations'] if 'n_permutations' in kwargs else 100
            total = total * parsed_cv + parsed_cv
        elif validation_curve:
            total = parsed_cv * len(args[2]) * 2
        elif SearchCV:
            if isinstance(self, model_selection.GridSearchCV):
                total = len(model_selection.ParameterGrid(self.param_grid))
            elif isinstance(self, model_selection.RandomizedSearchCV):
                total = self.n_iter
            total *= parsed_cv if self.cv is None else self.cv
        else:
            total = parsed_cv

        # `_save_me` is outside of try catch so in case something goes wrong in the try catch, whatever function/method (aka predict or score) we changed will go back to way it was no matter what
        _save_me = getattr(estimator.__class__, option)
        try:
            # This is "Option 1" of the roadmap; This tracks folds/cvs in several of the model_selection methods/functions
            with tclass(*targs, total=total, **tkwargs) as t:
                def update(self, func, *margs, **mkwargs):
                    assert callable(func), "func must a be function or method"
                    t.update()
                    return func(self, *margs, **mkwargs)
                setattr(estimator.__class__, option, functools.partialmethod(update, _save_me))

                if learning_curve:
                    final_func = 'learning_curve'
                elif permutation_test_score:
                    final_func = 'permutation_test_score'
                elif validation_curve:
                    final_func = 'validation_curve'
                else:
                    final_func = "cross_{}".format('validate' if validate else 'val_{}'.format(option))

                if SearchCV:
                    return self.fit(X, *args, **kwargs)

                return getattr(model_selection, final_func)(estimator, X, *args, **kwargs)
        finally:
            setattr(estimator.__class__, option, _save_me)

    # aliases for each tqdm version of the function
    cross_val_predict_alias = ['progress_cross_val_predict', 'pcvp', 'pcross_val_predict']
    cross_val_score_alias = ['progress_cross_val_score', 'pcvs', 'pcross_val_score']
    cross_validate_alias = ['progress_cross_validate', 'pcv', 'pcross_validate']
    learning_curve_alias = ['progress_learning_curve', 'plc', 'plearning_curve']
    permutation_test_score_alias = ['progress_permutation_test_score', 'ppts', 'ppermutation_test_score']
    validation_curve_alias = ['progress_validation_curve', 'pvc', 'pvalidation_curve']
    SearchCV_alias = ['progress_fit']

    aliases = cross_val_predict_alias \
            + cross_val_score_alias \
            + cross_validate_alias \
            + learning_curve_alias \
            + permutation_test_score_alias \
            + validation_curve_alias \
            + SearchCV_alias

    for name in aliases:
        if name in cross_val_predict_alias:
            option = 'predict'
        elif name in cross_val_score_alias:
            option = 'score'
        elif name in cross_validate_alias:
            option = 'validate'
        elif name in learning_curve_alias:
            option = 'learning_curve'
        elif name in permutation_test_score_alias:
            option = 'permutation_test_score'
        elif name in validation_curve_alias:
            option = 'validation_curve'
        elif name in SearchCV_alias:
            option = 'SearchCV'
            setattr(model_selection.GridSearchCV, name, functools.partialmethod(progress_cross_val, option))
            setattr(model_selection.RandomizedSearchCV, name, functools.partialmethod(progress_cross_val, option))
            continue

        setattr(model_selection, name, functools.partial(progress_cross_val, option))
