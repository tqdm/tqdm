@classmethod
def sklearn(tclass, *targs, **tkwargs):
    import functools
    import warnings
    from sklearn import model_selection
    # Maintainers do not forget to look at the default value of cv it may change over time and has changed in the past
    def progress_cross_val(option, estimator, X, *args, cv=5, **kwargs):
        if 'verbose' in kwargs and kwargs['verbose'] >= 1:
            warnings.warn('Using verbose with tqdm can cause display issues with tqdm and/or the verbose messages', category=SyntaxWarning)
        valid_options = ['predict', 'score', 'validate', 'learning_curve']
        assert option in valid_options, f"[tqdm: Internal] progress_cross_val() {option} not in valid options"
        option, validate = ('score', True) if option == 'validate' else (option, False)
        option, learning_curve = ('score', True) if option == 'learning_curve' else (option, False)

        # TODO: Currently only supports cv as input if it's an int, need to support the other input types (CV splitter and iterable)
        if 'total' in kwargs:
            # Maybe remove this? IDK
            total = twargs['total']
        elif learning_curve:
            total = 2 * len(kwargs['train_sizes']) * cv if 'train_sizes' in kwargs else cv * 5 * 2 # For some reason there is a mysterious two that needs to be multiplied; five is the default length of `train_sizes`
        else:
            total = cv

        # `_save_me` is outside of try catch so in case something goes wrong, whatever function/method (aka predict or score) we changed will go back to way it was no matter what
        _save_me = getattr(estimator.__class__, option)
        try:
            # This "Option 1" of roadmap; This tracks folds/cvs in several of the model_selection methods/functions
            with tclass(*targs, total=total, **tkwargs) as t:
                def update(self, func, *margs, **mkwargs):
                    assert callable(func), "func must a be function or method"
                    t.update()
                    return func(self, *margs, **mkwargs)
                setattr(estimator.__class__, option, functools.partialmethod(update, _save_me))
                return getattr(model_selection, 'learning_curve' if learning_curve else f"cross_{'validate' if validate else f'val_{option}'}")(estimator, X, *args, cv=cv, **kwargs)
        finally:
            setattr(estimator.__class__, option, _save_me)

    # aliases for each tqdm version of the function
    cross_val_predict_alias = ['progress_cross_val_predict', 'pcvp', 'pcross_val_predict']
    cross_val_score_alias = ['progress_cross_val_score', 'pcvs', 'pcross_val_score']
    cross_validate_alias = ['progress_cross_validate', 'pcv', 'pcross_validate']
    learning_curve_alias = ['progress_learning_curve', 'plc', 'plearning_curve']
    for name in cross_val_predict_alias + cross_val_score_alias + cross_validate_alias + learning_curve_alias:
        if name in cross_val_predict_alias:
            option = 'predict'
        elif name in cross_val_score_alias:
            option = 'score'
        elif name in cross_validate_alias:
            option = 'validate'
        elif name in learning_curve_alias:
            option = 'learning_curve'
        setattr(model_selection, name, functools.partial(progress_cross_val, option))
