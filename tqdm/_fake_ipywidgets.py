from IPython.display import HTML as _HTML, ProgressBar as _ProgressBar, DisplayHandle
from binascii import b2a_hex, b2a_base64, hexlify
import os


def _new_id():
    """Generate a new random text id with urandom"""
    return b2a_hex(os.urandom(16)).decode('ascii')


class _Layout(dict):
    def __init__(self, *args, **kwargs):
        return super(_Layout, self).__init__(*args, **kwargs)

    def __key(self, key):
        return "" if key is None else key.lower()

    def __setattr__(self, key, value):
        self[self.__key(key)] = value

    def __getattr__(self, key):
        return self.get(self.__key(key))

    def __getitem__(self, key):
        return super(_Layout, self).get(self.__key(key))

    def __setitem__(self, key, value):
        return super(_Layout, self).__setitem__(self.__key(key), value)

    def __repr__(self):
        expr = ''
        for key in self:
            expr += key+':'+str(self[key])+';'
        return expr


class IntProgress(_ProgressBar):
    def __init__(self, max=1, value=0, min=0, description='', bar_style=''):
        self.min = min
        self.description = description
        self._bar_style = ''
        self.bar_style = bar_style

        self.style = _Layout()
        self.layout = _Layout()
        self.parent = None
        self.display_id = _new_id()
        super(IntProgress, self).__init__(total=max)
        self._progress = value

    @property
    def bar_style(self):
        return self._bar_style

    @bar_style.setter
    def bar_style(self, value):
        if value in ['success', 'info', 'warning', 'danger', '']:
            self._bar_style = value
        else:
            raise EnvironmentError(
                "bar_style should in ['success', 'info', 'warning', 'danger', '']")

    @property
    def value(self):
        return self._progress

    @value.setter
    def value(self, v):
        self._progress = v
        self.update()

    def display(self):
        if self.parent is None:
            super(IntProgress, self).display()
        else:
            self.parent.display()

    def update(self):
        if self.parent is None:
            super(IntProgress, self).update()
        else:
            self.parent.update()

    def _repr_html_(self):
        return "<progress style='width:{};padding:10px;' max='{}' value='{}'></progress>".format(
            self.html_width, self.total, self.progress)


class HTML(_HTML):
    def __init__(self, data=''):
        super(HTML, self).__init__(data)
        self.parent = None

    @property
    def value(self):
        return self.data

    @value.setter
    def value(self, v):
        self.data = v
        self.update()

    def display(self):
        if self.parent is None:
            super(HTML, self).display()
        else:
            self.parent.display()

    def update(self):
        if self.parent is None:
            super(HTML, self).update()
        else:
            self.parent.update()


class HBox(_HTML):
    def __init__(self, children=()):
        self._children = {}
        self.children = children
        self.layout = _Layout()
        self._data = ''
        self.display_id = _new_id()
        super(HBox, self).__init__()

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, _children):
        for obj in _children:
            obj.parent = self
        self._children = _children

    @property
    def data(self):
        style = "display:flex;flex-direction:row;"
        style += str(self.layout)
        s = '<div style="'+style+'">'
        for i in self.children:
            s += i._repr_html_()
        s += '</div>'
        return s

    @data.setter
    def data(self, value):
        # disabled
        pass

    def display(self):
        display(self, display_id=self.display_id)

    def update(self):
        display(self, display_id=self.display_id, update=True)

    def close(self):
        self.children = ()
        display(HTML(''), display_id=self.display_id, update=True)
