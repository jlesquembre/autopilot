import os
import curses
from curses import panel
from enum import Enum

import sarge

from . import validate
from . import utils
from .exceptions import InvalidOption, NoValidatorError


class CursesManager:

    def __enter__(self):
        self.is_setup = True
        self.win = curses.initscr()
        self.panel = panel.new_panel(self.win)
        self.on()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.off()

    def on(self):
        self.win.leaveok(0)
        self.win.keypad(1)
        curses.cbreak()
        curses.noecho()
        os.environ['ESCDELAY'] = '25'   # don't know a cleaner way
        try:
            start_color()
        except:
            pass

    def off(self):
        """Turn off curses"""
        self.win.keypad(0)
        curses.nocbreak()
        curses.echo()
        try:
            curses.curs_set(1)
        except:
            pass
        curses.endwin()

    def open_editor(self, editor, path=None):
        self.off()
        command = '{} {}'.format(editor, path) if path else editor
        process = sarge.run(command)
        # TODO wait until editor is closed
        #process = sarge.run('gvim')
        #process.wait()
        self.on()
        curses.curs_set(0)


def handle_form(form, ok_button, cancel_button, ui=None):

    form.add(ok_button, attached=False)
    form.add(cancel_button, attached=False)

    form.render()

    while True:

        panel.update_panels()
        curses.doupdate()

        ret = form.handle_key(form.win.getch())
        form.clean_popup()

        if ret == ok_button.label:

            try:
                return form.validator(form.data, form.config)
            except InvalidOption as e:
                form.show_popup(ErrorPopup(str(e)))
            except NoValidatorError:
                return form.data

        elif ret == cancel_button.label:
            return 'Cancel, nothing to do!'


def handle_input(win, scroll_mode=True):
    key = win.getch()
    if not scroll_mode:
        return key
    elif key == curses.KEY_UP:
        return 'up'
    elif key == curses.KEY_DOWN:
        return 'down'
    # elif key == curses.KEY_ENTER:
    elif key == ord('\n'):
        return 'enter'


def _update_next_version(widget):
    def call(release_version):
        try:
            widget.text = utils.get_next_dev_version(release_version)
            widget.refresh()
        except:  # If release_version in not valid, don't update dev version
            pass
    return call


def _update_open_changelog(ui, version, tmp_dir, editor, project_dir):
    def f():
        changelog_path = utils.update_changelog(project_dir/'CHANGES.rst', dest_dir=tmp_dir, version=version.value)
        ui.open_editor(editor=editor, path=changelog_path )
    return f


class Color(Enum):
    bold = curses.A_BOLD
    dim = curses.A_DIM
    reverse = curses.A_REVERSE
    standout = curses.A_STANDOUT
    underline = curses.A_UNDERLINE
    none = 0


# TODO need to be more generic
class TermStr:

    def __init__(self, *args):
        self.args = args

    def addstr(self, win, y=0, x=0):
        pos = x
        attr = Color.none

        for arg in self.args:
            if type(arg) is Color:
                attr = arg
            elif type(arg) is str:
                if attr == Color.none:
                    win.addstr(y, pos, arg)
                else:
                    win.addstr(y, pos, arg, attr.value)

                pos += len(arg)

    def __len__(self):
        return sum([len(x) for x in self.args if type(x) is str])


class Box:
    def __init__(self, y=0, x=0, lines=None, cols=None, label=None):
        if lines is None:
            lines = curses.LINES
        if cols is None:
            cols = curses.COLS

        self.win = curses.newwin(lines, cols, y, x)
        self.panel = panel.new_panel(self.win)
        self.win.box()

        if label:
            self.win_l = curses.newwin(1, len(label) + 2, y, x + 1)
            self.panel_l = panel.new_panel(self.win_l)
            if type(label) is str:
                label = TermStr(label)
            label.addstr(self.win_l, 0, 1)


class Margin(object):

    def __init__(self, margin=None, top=0, right=0, bottom=0, left=0, lines=None, cols=None):
        if cols:
            self.right = self.left = cols
        if lines:
            self.top = self.bottom = lines

        if top:
            self.top = top
        if right:
            self.right = right
        if bottom:
            self.bottom = bottom
        self.left = left

        if margin and not top and not right and not bottom and not left and not cols and not lines:
            self.top = self.right = self.bottom = self.left = margin

    @property
    def lines(self):
        return self.top + self.bottom

    @property
    def cols(self):
        return self.right + self.left


class Widget(object):

    def handle_key(self, key):
        k = None

        if key == curses.KEY_UP:
            k = '_up'
        elif key == curses.KEY_DOWN:
            k = '_down'
        elif key == ord('\n'):
            k = '_enter'
        elif key == ord(' '):
            k = '_printable' if hasattr(self, '_printable') else '_space'
        elif key in range(32, 256) or key == curses.KEY_BACKSPACE:
            k = '_printable'

        subwidget = self.get_subwidget()

        if k in dir(type(self)) and not getattr(subwidget, 'handle_input', False):
            if k == '_printable':
                return getattr(self, k)(key)
            else:
                return getattr(self, k)()

        elif subwidget:
            return subwidget.handle_key(key)

    def get_subwidget(self):
        if hasattr(self, 'popup'):
            return self.popup
        if hasattr(self, 'widgets'):
            return self.widgets[self.current]
        elif hasattr(self, 'widget'):
            return self.widget

    @property
    def handle_input(self):
        return False

    @property
    def read_only(self):
        return getattr(self, '_read_only', False)

    def get_value(self):
        subwidget = self.get_subwidget()
        if subwidget:
            return getattr(subwidget, 'value', subwidget.get_value())


class ErrorPopup(Widget):
    def __init__(self, text):

        text_lines = text.split('\n')

        y = int(curses.LINES/2)
        x = int(curses.COLS/2)

        lines = 5 + len(text_lines)
        cols = max(map(len, text_lines)) + 4

        self.win = curses.newwin(lines, cols, y-lines//2, x-cols//2)
        self.panel = panel.new_panel(self.win)

        self.win.box()

        for i, line in enumerate(text_lines):
            self.win.addstr(2 + i, 2, line)
        self.win.addstr(4 + i, 2, ' OK ', curses.A_REVERSE)

        self.panel.top()
        self.panel.show()

    def _enter(self):
        self.panel.hide()
        del self.win
        self.deleteme = True

    def handle_input(self):
        return True


class SelectOptionPopup(Widget):
    def __init__(self, options, current=0):
        self.y = int(curses.LINES/2)
        self.x = int(curses.COLS/2)

        self.cols = max([len(option) for option in options]) + 2
        self.current = current
        self.margin = Margin(1)

        self.options = options

        lines = len(self.options) + self.margin.lines
        cols = self.cols + self.margin.cols

        self.win = curses.newwin(lines, cols, self.y-lines//2, self.x-cols//2)
        self.panel = panel.new_panel(self.win)

        for i, option in enumerate(self.options):
            self.win.addstr(i+self.margin.top, self.margin.left, ' {}'.format(option))

        self.win.box()
        self.panel.hide()

    def focus(self):
        curses.curs_set(0)
        self.win.chgat(self.current+self.margin.top, self.margin.left, self.cols, curses.A_REVERSE)
        self.panel.show()

    def unfocus(self):
        self.win.chgat(self.current+self.margin.top, self.margin.left, self.cols, curses.A_NORMAL)

    def _up(self):
        self.unfocus()
        self.current -= 1
        if self.current < 0:
            self.current = len(self.options) - 1
        self.focus()

    def _down(self):
        self.unfocus()
        self.current += 1
        if self.current >= len(self.options):
            self.current = 0
        self.focus()

    def enter(self):
        self.panel.hide()

    def hide(self):
        self.panel.hide()

    @property
    def value(self):
        return self.options[self.current]


class SelectOptionPanel(Widget):
    def __init__(self, options, current=0, y=0, x=0):
        self.popup = SelectOptionPopup(options, current)
        self.popup_visible = False
        self.y = y
        self.x = x
        self.win = None
        self.refresh()

    def refresh(self):
        if self.win:
            del self.win

        label = self.popup.value

        self.win = curses.newwin(1, len(label) + 2, self.y, self.x)
        self.win.addstr(0, 1, label)

        self.panel = panel.new_panel(self.win)
        self.panel.show()

    def focus(self):
        curses.curs_set(0)
        self.win.chgat(0, 0, curses.A_REVERSE)

    def unfocus(self):
        self.win.chgat(curses.A_NORMAL)

    def _enter(self):
        if self.popup_visible:
            self.refresh()
            self.popup.hide()
            self.focus()
        else:
            self.popup.focus()

        self.popup_visible = not self.popup_visible

    @property
    def handle_input(self):
        return self.popup_visible


class TextPanel(Widget):
    def __init__(self, text, y=0, x=0):
        # Last value was added to handle the on_change, maybe can be moved to a
        # parent class
        self._last_value = self.text = text
        self.y = y
        self.x = x

        self.refresh()

    def refresh(self):
        self.win = curses.newwin(1, len(self.text) + 2, self.y, self.x)
        self.win.addstr(0, 1, self.text)

        self.panel = panel.new_panel(self.win)
        self.panel.show()

    def focus(self):
        self._last_value = self.value
        self.panel.top()
        curses.curs_set(1)

    def unfocus(self):
        curses.curs_set(0)
        if self._last_value != self.value and hasattr(self, 'on_change'):
            self.on_change(self.value)

    def _printable(self, key):
        if key == curses.KEY_BACKSPACE:
            self.text = self.text[:-1]
        else:
            self.text += chr(key)

        del self.win
        self.refresh()

    @property
    def value(self):
        return self.text


class RadioButton(Widget):
    def __init__(self, selected=True, y=0, x=0):
        self.selected = selected
        self.y = y
        self.x = x

        self.refresh()

    def refresh(self):
        self.win = curses.newwin(1, 5, self.y, self.x)
        self.win.addstr(0, 1, '[{}]'.format('X' if self.value else ' '))
        self.win.move(0, 2)

        self.panel = panel.new_panel(self.win)
        self.panel.show()

    def focus(self):
        self.panel.top()
        curses.curs_set(1)

    def unfocus(self):
        curses.curs_set(0)

    @property
    def value(self):
        return self.selected

    def _enter(self):
        self.selected = not self.selected
        self.refresh()

    def _space(self):
        self._enter()


class FormEntrySelector(Widget):

    padding = 2
    lines = 1  # This widget has only one line

    def __init__(self, label, widget=None, y=0, x=0, read_only=False, extra_lines=0):
        self.label = label
        self.y = y
        self.x = x
        self.widget = widget
        self._read_only = read_only
        self.cols = len(self.label) + self.padding
        self.win = None
        self.lines = self.lines + extra_lines

    def refresh(self):
        if self.win:
            del self.win

        self.win = curses.newwin(1, self.cols, self.y, self.x)
        self.win.addstr(0, 1, self.label)
        self.panel = panel.new_panel(self.win)
        self.panel.show()

        if self.widget:
            self.widget.refresh()

    def label_len(self):
        return len(self.label)

    def focus(self):
        self.widget.focus()

    def unfocus(self):
        self.widget.unfocus()

    @property
    def handle_input(self):
        return self.widget.handle_input


class Button(Widget):

    padding = 2
    lines = 1

    def __init__(self, label, y=0, x=0, on_enter=None, extra_lines=0):
        self.widget = None
        self.label = label
        self.y = y
        self.x = x
        self.on_enter = label if on_enter is None else on_enter

        self.cols = len(label) + 2
        self.lines = self.lines + extra_lines

        self.refresh()

    def focus(self):
        curses.curs_set(0)
        self.win.chgat(0, 0, curses.A_REVERSE)

    def unfocus(self):
        self.win.chgat(curses.A_NORMAL)

    def _enter(self):
        try:
            return self.on_enter()
        except TypeError:
            return self.on_enter

    def label_len(self):
        return len(self.label)

    def refresh(self):
        if getattr(self, 'win', None):
            del self.win

        self.win = curses.newwin(1, self.cols, self.y, self.x)
        self.win.addstr(0, 1, self.label)

        self.panel = panel.new_panel(self.win)
        self.panel.show()



class Form(Widget):

    def __getattr__(self, name):
        # if this function is called, is because the attribute called "name"
        # was not found in the instance, nor the class
        if name == 'validator':
            raise NoValidatorError
        self.__getattribute__(name)
        # super().__getattribute__(name)

    def __init__(self, win, margin=None, y_space=1):
        self.widgets = []
        self.attached_widgets = []
        self.win = win
        self.y_space = y_space

        self.margin = margin if margin else Margin(1)
        self.y, self.x = win.getbegyx()
        self.y += self.margin.top
        self.x += self.margin.left
        self.current = 0

    def add(self, widget, attached=True):
        self.widgets.append(widget)
        if attached:
            self.attached_widgets.append(widget)

    def render(self, current=None):
        cols = max([w.label_len() for w in self.attached_widgets], default=0)
        for w in self.attached_widgets:
            w.y = self.y
            w.x = self.x

            self.y += self.y_space + w.lines

            if w.widget:
                w.widget.x = cols + w.x + w.padding
                w.widget.y = w.y

            w.refresh()

        if current is not None:
            self.current = current
        if self.current < 0:
            self.current = len(self.widgets) + self.current

        self.widgets[self.current].focus()

    def _up(self):
        cur = self.widgets[self.current]
        cur.unfocus()
        self.current -= 1
        if self.current < 0:
            self.current = len(self.widgets) - 1

        if self.widgets[self.current].read_only:
            self._up()
        else:
            self.widgets[self.current].focus()

    def _down(self):
        cur = self.widgets[self.current]
        cur.unfocus()
        self.current += 1
        if self.current >= len(self.widgets):
            self.current = 0

        if self.widgets[self.current].read_only:
            self._down()
        else:
            self.widgets[self.current].focus()

    @property
    def data(self):
        return {(w.label.lower().replace(' ', '_')): w.get_value()
                for w in self.attached_widgets}

    def show_popup(self, popup):
        self.popup = popup

    def clean_popup(self):
        try:
            if self.popup.deleteme:
                del self.popup
        except AttributeError:
            pass


def release_ui(config):

    with CursesManager() as ui:

        version, next_version = utils.get_next_versions(config['current_version'])

        _box = Box(label=TermStr('Project: ', Color.bold, config['project_name']))

        form = Form(ui.win, margin=Margin(top=3, left=2))

        release_version_textpanel = TextPanel(version)
        next_version_textpanel = TextPanel(next_version)
        release_version_textpanel.on_change = _update_next_version(next_version_textpanel)

        form.add(FormEntrySelector('Current version', TextPanel(config['current_version']), read_only=True))
        form.add(FormEntrySelector('Release version', release_version_textpanel))
        form.add(FormEntrySelector('Next dev version', next_version_textpanel, extra_lines=1))

        form.current = -2
        form.config = config
        form.validator = validate.validate_release

        tmp_dir = config['tmp_dir']
        vim_button = Button('Preview changelog', extra_lines=1,
                        on_enter=_update_open_changelog(ui, release_version_textpanel, tmp_dir,
                                                        editor=config['editor'], project_dir=config['project_dir']))
        #form.add(vim_button, attached=False)
        form.add(vim_button)

        form.add(FormEntrySelector('Git push',
                                   RadioButton(selected=config['release']['push'])))
        form.add(FormEntrySelector('Upload to PyPI',
                                   SelectOptionPanel(options=config['pypi_list'],
                                                     current=config['release']['upload'])))

        return handle_form(form, ok_button=Button('Release', 19, 1),
                           cancel_button=Button('Cancel', 19, 11), ui=ui)


def new_project_ui(config):
    with CursesManager() as ui:

        _box = Box(label=TermStr(Color.bold, 'Create new project'))

        form = Form(ui.win, margin=Margin(top=3, left=2))

        project_name = config['new_project']['project_name']

        form.add(FormEntrySelector('User name', TextPanel(config['author']['name'])))
        form.add(FormEntrySelector('User email', TextPanel(config['author']['email'])))
        form.add(FormEntrySelector('Project name', TextPanel(project_name)))
        form.add(FormEntrySelector('Directory', TextPanel(config['new_project']['default_dir'])))
        form.add(FormEntrySelector('License',
                                   SelectOptionPanel(options=utils.get_licenses(),
                                                     current=config['new_project']['license'])))
        form.add(FormEntrySelector('Initial commit',
                                   RadioButton(selected=config['new_project']['commit'])))

        form.current = (-2 if project_name else 2)
        form.config = config
        form.validator = validate.validate_new_project

        return handle_form(form, ok_button=Button('Create', 17, 1),
                           cancel_button=Button('Cancel', 17, 9))
