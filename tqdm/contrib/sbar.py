from tqdm.autonotebook import tqdm
from typing import NamedTuple

class ProgressStep(NamedTuple):
    num: int    
    val: int=1
    sub: int=None     
    desc:str=''

class sbar(tqdm):
    '''
    What is this and why might it be under tqdm.contrib?
    sbar is a subclass of `tqdm.autonotebook.tqdm` to make using non-iterables
    steps easier. 

    It takes a list of "steps". 
    
    "Wait, didn't you say it was for non-iterables?"
    Yup.
    For example, suppose you have a pytorch_lightning.LightningDataModule
    ```python
    class MyDM(pl.LightningDataModule):
        _STEPS = [...]
        def __init__(self, *args, **kwargs):
            # ...
            self.sbar(self._STEPS, desc='MyDM')

        ...
        
    ```

    and you call the `prepare` method which downloads and transforms data.
    You can easily see where you might have several non-standard methods
    that are part of a pipeline, which might time some time to resolve. 
    You can now have a `sbar` instance living inside you class and more easily
    move between "steps" of the preprocessing pipeline (method calls)

    e.g.

    ```python
    _STEPS = [     
        ProgressStep(1, 20, desc='download'),

        ProgressStep(2, 5, 0, desc='load_timepoints'),
        ProgressStep(2, 5, 1, desc='load_timepoints'),
        ProgressStep(2, 5, 2, desc='load_timepoints'),
        ProgressStep(2, 5, 3, desc='load_timepoints'),
        ProgressStep(2, 5, 4, desc='load_timepoints'),
        # ProgressStep(2, val=25, desc='load_timepoints'), # <-- doesn't need to be explicitly stated

        ProgressStep(3, 5, 0, desc='data_wrangling'),
        ProgressStep(3, 5, 1, desc='data_wrangling'),
        ProgressStep(3, 5, 2, desc='data_wrangling'),
        ProgressStep(3, 5, 3, desc='data_wrangling'),
        ProgressStep(3, 5, 4, desc='data_wrangling'),
        # ProgressStep(3, val=25, desc='data_wrangling'),

        ProgressStep(4, 5, desc='merge_data'),

        ProgressStep(5, 5, 0, desc='filter_data'),
        ProgressStep(5, 5, 1, desc='filter_data'),
        ProgressStep(5, 5, 2, desc='filter_data'),
        ProgressStep(5, 5, 3, desc='filter_data'),
        ProgressStep(5, 5, 4, desc='filter_data'),
        ProgressStep(5, 5, 5, desc='filter_data'),
        # ProgressStep(5, val=30, desc='filter_data'),

        ProgressStep(6, 20, desc='embed'),

        ProgressStep(7, desc='save'),
    ]

    ```
    
    which can be used inside the `MyDM` class like:

    ```python
    # inside MyDM class delcaration
    def prepare(self):
        # ...
        self.sbar.write('Downloading data')
        self.sbar.step(1)
        
        # ...
        self.sbar.write('Loading datafiles')
        for i in range(5):
            self.sbar.step(2, i)    # <--- handles substeps
        
        # ...

        # ...
        self.sbar.step(7)                
    ```

    Yes the `_STEPS` list is an iterable and technically compatible with
    `tqdm` _as is_. However, handling abstract method calling sounds like 
    a larger pain than this.
    
    
    '''
    __NUM_IDX = 0    
    __SUB_IDX = 2
    __VAL_IDX = 1
    
    def __init__(self, steps, *args, **kwargs):
        self.steps = steps        
        super(sbar, self).__init__(*args, total=self.pbar_total, **kwargs)
        
        
    def _num(self, step):
        return step[self.__NUM_IDX]
    
    def _val(self, step):
        return step[self.__VAL_IDX]
    
    def _sub(self, step):
        return step[self.__SUB_IDX]
        
    def step(self, num:int, sub:int=None):
        pval = self.calc_pbar_val(num, sub)
        self.n = pval
        self.refresh()
        
    @property
    def pbar_total(self):
        total = sum([
            self.sum_subs(num)
            for num in self.step_nums 
        ])
        return total
    
    @property
    def step_nums(self):
        return self._slist([self._num(step) for step in self.steps])
    
    @property
    def num_main_steps(self):
        return len(self.step_nums)
    
    @property
    def num_all_steps(self):
        total = 0
        for num, subs in self.step_subs.items():
            total += 1 + len(subs)
        return total
    
    @property
    def step_subs(self):
        return {
            num: self.get_step_subs(num)
            for num in self.step_nums
        }
           
    def get_step(self, num:int, sub:int=None) -> Union[ProgressStep, None]:
        for step in self.steps:
            if self.does_step_match(step, num, sub):
                return step
        return None

    def get_step_subs(self, num):
        return self._slist([
            self._sub(step)
            for step in self.steps
            if self._num(step) == num and self._sub(step) is not None
        ])
    
    def step_val_from_subs(self, num):
        step = self.get_step(num)
        if step is not None:
            return self._val(step)
        
        subs = self.step_subs[num]
        total = 0
        for sub in subs:
            step = self.get_step(num, sub)
            total += self._val(step)
        return total
        

    def _slist(self, arr):
        return sorted(list(set(arr)))

    def does_num_match(self, step, num:int):
        return self._num(step) == num
    
    def does_sub_match(self, step, sub:int):
        return self._sub(step) == sub
    
    def does_step_match(self, step, num:int, sub:int):
        num_q = self.does_num_match(step, num)
        sub_q = self.does_sub_match(step, sub)
        return num_q and sub_q
    
    def does_step_exist(self, num:int, sub:int=None) -> bool:
        step = self.get_step(num, sub)
        return step is not None
    
    def sum_subs(self, num:int):
        step = self.get_step(num)
        if step is not None:
            return self._val(step)
        
        subs = self.step_subs[num]
        total = 0
        for sub in subs:
            step = self.get_step(num, sub)
            total += self._val(step)
        return total
    
    def calc_pbar_val(self, num:int, sub:int=None) -> int:
        total = 0
        
        exists_q = self.does_step_exist(num, sub)
        # if no substep, map to main step
        if sub is not None:            
            if not exists_q:
                sub = None
        
        if num not in self.step_nums:
            if num > self.num_all_steps:
                return self.pbar_total
            elif num > self.num_main_steps:
                return self.pbar_total
            elif num > max(self.step_nums):
                return self.pbar_total            
            return total
        
        for snum in self.step_nums:
            if snum < num:
                sval = self.sum_subs(snum)
                total += sval
                continue
                
            elif snum > num:
                continue
            
            
            subs = self.step_subs[num]
            if len(subs) == 0:
                total += self.sum_subs(num)
                continue
                
            for ssub in subs:
                step = self.get_step(num, ssub)
                total += self._val(step)
                                                        
        return total