@classmethod
def sklearn(tclass, *targs, **tkwargs):
    import collections.abc, types
    import functools
    import warnings
    from sklearn import model_selection
    # Maintainers do not forget to look at the default value of cv it may change over time and has changed in the past
    def progress_cross_val(option, estimator, X, *args, cv=5, **kwargs):
        if 'verbose' in kwargs and kwargs['verbose'] >= 1:
            warnings.warn('Using verbose with tqdm can cause display issues with tqdm and/or the verbose messages', category=SyntaxWarning)
        valid_options = ['predict', 'score', 'validate',
                        'learning_curve', 'permutation_test_score',
                        'validation_curve']
        assert option in valid_options, f"[tqdm: Internal] progress_cross_val() {option} not in valid options"

        option, validate = ('score', True) if option == 'validate' else (option, False)
        option, learning_curve = ('score', True) if option == 'learning_curve' else (option, False)
        option, permutation_test_score = ('score', True) if option == 'permutation_test_score' else (option, False)
        option, validation_curve = ('score', True) if option == 'validation_curve' else (option, False)

        if hasattr(cv, 'n_splits'):
            parsed_cv = cv.n_splits
        elif isinstance(cv, collections.abc.Iterable) or isinstance(cv, types.GeneratorType):
            parsed_cv = len(list(cv))
        else:
            parsed_cv = cv

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
        else:
            total = parsed_cv

        # `_save_me` is outside of try catch so in case something goes wrong in the try catch, whatever function/method (aka predict or score) we changed will go back to way it was no matter what
        _save_me = getattr(estimator.__class__, option)
        try:
            # This "Option 1" of the roadmap; This tracks folds/cvs in several of the model_selection methods/functions
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
                    final_func = f"cross_{'validate' if validate else f'val_{option}'}"

                return getattr(model_selection, final_func)(estimator, X, *args, cv=cv, **kwargs)
        finally:
            setattr(estimator.__class__, option, _save_me)

    # aliases for each tqdm version of the function
    cross_val_predict_alias = ['progress_cross_val_predict', 'pcvp', 'pcross_val_predict']
    cross_val_score_alias = ['progress_cross_val_score', 'pcvs', 'pcross_val_score']
    cross_validate_alias = ['progress_cross_validate', 'pcv', 'pcross_validate']
    learning_curve_alias = ['progress_learning_curve', 'plc', 'plearning_curve']
    permutation_test_score_alias = ['progress_permutation_test_score', 'ppts', 'ppermutation_test_score']
    validation_curve_alias = ['progress_validation_curve', 'pvc', 'pvalidation_curve']

    aliases = cross_val_predict_alias \
            + cross_val_score_alias \
            + cross_validate_alias \
            + learning_curve_alias \
            + permutation_test_score_alias \
            + validation_curve_alias

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
        setattr(model_selection, name, functools.partial(progress_cross_val, option))
