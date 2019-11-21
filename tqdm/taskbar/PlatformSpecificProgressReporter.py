class PlatformSpecificProgressReporter:
    def __init__(self, total:int=None, unit:str=""):
        raise NotImplementedError()
    
    def progress(self, current:int, speed:float):
        raise NotImplementedError()
    
    def message(self, msg:str):
        pass
    
    def prefix(self, prefix:str):
        pass

    def postfix(self, postfix:str):
        pass
    
    def fail(self, reason:str=None):
        raise NotImplementedError()
    
    def clear(self):
        raise NotImplementedError()
    
    def __enter__(self):
        raise NotImplementedError()
    
    def __exit__(self, exception_type, exception_value, traceback):
        raise NotImplementedError()

class DummyProgressReporter(PlatformSpecificProgressReporter):
    """Used instead of the progress reporter using unsupported features"""
    def __init__(self, total:int=None, unit:str=""):
        pass
    
    def progress(self, current:int, speed:float):
        pass
    
    def fail(self, reason:str=None):
        pass
    
    def success(self):
        pass
    
    def clear(self):
        pass
    
    def __enter__(self):
        pass
    
    def __exit__(self, exception_type, exception_value, traceback):
        pass
