from IPython.display import HTML as _HTML, ProgressBar as _ProgressBar
from binascii import b2a_hex, hexlify
import os

if True:  # pragma: no cover
    def _new_id():
        """Generate a new random text id with urandom"""
        return b2a_hex(os.urandom(16)).decode('ascii')

    def _k(key):
        return "" if key is None else key.lower()

    class _Layout(dict):
        """CSS Layout"""

        def __init__(self, *args, **kwargs):
            super(_Layout, self).__init__(*args, **kwargs)

        def __setattr__(self, key, value):
            self[_k(key)] = value

        def __getattr__(self, key):
            return self.get(_k(key))

        def __getitem__(self, key):
            return super(_Layout, self).get(_k(key))

        def __setitem__(self, key, value):
            return super(_Layout, self).__setitem__(_k(key), value)

        def __repr__(self):
            expr = ''
            for key in self:
                expr += key+':'+str(self[key])+';'
            return expr

    class IntProgress(_ProgressBar):
        """Weaker implementation of ipywidgets.IntProgress"""

        def __init__(self, max=1, value=0, min=0, description='', bar_style=''):
            """
            Parameters
            ----------
            max: int, optional
                The maximum progress.
            value: int, optional
                The current progress.
            min: int, optional
                The minimum progress
            description: str, optional
                The description text at the starting position.
            bar_stype: str, option
                Not implemented. Just for compatibility 
            """
            self.min = min
            self.description = description
            self._bar_style = ''
            self.bar_style = bar_style

            self.parent = None
            self.style = _Layout()
            self.layout = _Layout()
            self.display_id = _new_id()
            super(IntProgress, self).__init__(total=max)
            self._progress = value

            self.style.margin = '2px 4px'

        @property
        def bar_style(self):
            """The style of the progress bar. Not implemented"""
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
            """The current progress"""
            return self._progress

        @value.setter
        def value(self, v):
            self._progress = v
            self.update()

        def display(self):
            """Display the object"""
            if self.parent is None:
                super(IntProgress, self).display()
            else:
                self.parent.display()

        def update(self):
            """Refresh the object in the display area"""
            if self.parent is None:
                super(IntProgress, self).update()
            else:
                self.parent.update()

        def _repr_desc_(self):
            return "<span>{}</span>".format(self.description)

        def _repr_bar_(self):
            return "<progress style='{}' max='{}' value='{}'></progress>".format(
                str(self.style)+str(self.layout), self.total, self.progress)

        def _repr_html_(self):
            return self._repr_desc_() + self._repr_bar_()

    class HTML(_HTML):
        """Weaker implementation of ipywidgets.HTML"""

        def __init__(self, data=''):
            """
            Parameters
            ----------
            data: str, optional
                The HTML text.
            """
            super(HTML, self).__init__(data)
            self.parent = None

        @property
        def value(self):
            """The HTML text."""
            return self.data

        @value.setter
        def value(self, v):
            self.data = v
            self.update()

        def display(self):
            """Display the object"""
            if self.parent is None:
                super(HTML, self).display()
            else:
                self.parent.display()

        def update(self):
            """Refresh the object in the display area"""
            if self.parent is None:
                super(HTML, self).update()
            else:
                self.parent.update()

    class HBox(_HTML):
        """Weaker implementation of ipywidgets.HBox"""

        def __init__(self, children=()):
            """
            Parameters
            ----------
            children: iterable, optional
                The display objects.
            """
            self._children = {}
            self.children = children
            self.layout = _Layout()
            self._data = ''
            self.display_id = _new_id()
            super(HBox, self).__init__()

        @property
        def children(self):
            """The objects contained by Hbox"""
            return self._children

        @children.setter
        def children(self, _children):
            for obj in _children:
                obj.parent = self
            self._children = _children

        @property
        def data(self):
            """The formatted HTML"""
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
            """Display the box"""
            display(self, display_id=self.display_id)

        def update(self):
            """Update the box"""
            display(self, display_id=self.display_id, update=True)

        def close(self):
            """Clean the Hbox"""
            self.children = ()
            display(HTML(''), display_id=self.display_id, update=False)
