from .auto import tqdm as tqdm_auto
__author__ = {"github.com/": ["casperdcl"]}
__all__ = ['tqdm_async', 'tqdm']


class tqdm_async(tqdm_auto):
    def __init__(self, iterable=None, *args, **kwargs):
        super(tqdm_async, self).__init__(iterable, *args, **kwargs)
        self.iterable_awaitable = False
        if iterable is not None:
            if hasattr(iterable, "__anext__"):
                self.iterable_next = iterable.__anext__
                self.iterable_awaitable = True
            elif hasattr(iterable, "__next__"):
                self.iterable_next = iterable.__next__
            else:
                self.iterable_iterator = iter(iterable)
                self.iterable_next = self.iterable_iterator.__next__

    def send(self, *args, **kwargs):
        return self.iterable.send(*args, **kwargs)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            if self.iterable_awaitable:
                res = await self.iterable_next()
            else:
                res = self.iterable_next()
            self.update()
            return res
        except StopIteration:
            self.close()
            raise StopAsyncIteration
        except:
            self.close()
            raise


# Aliases
tqdm = tqdm_async
