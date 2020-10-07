# misc.py
#
# Copyright 2020 bunsenmurder
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, GObject, Gio, GLib
from enum import Enum
from pathlib import Path
from importlib.util import find_spec

class NotifStack(Enum):
    BUTTON = "Button"
    SPIN = "Spinner"

class Notifier():
    """ Notifier abstract class for showing notifications in Gtk GUI.
    This class assumes that the initializing container has a GtkBox as
    it's first child and a GtkLabel as one of it's children, with any
    descendants of the box being limited to one widget type per descendant.
    This is done so that widgets are accessed by type instead of any
    specific class atrributes.

    :param Gtk.Container top_container: Container instance object
    """
    def __init__(self, top_container):
        self.container = top_container
        self.to_id = None # Time out ID
        self.item_map = {}
        for item in self.container.get_children()[0].get_children():
            self.item_map.update({type(item).__name__: item})
            if hasattr(item, 'get_children'):
                for child in item.get_children():
                    self.item_map.update({type(child).__name__: child})

    def notify_abstract(self, text, time):
        if self.to_id:
            GLib.source_remove(self.to_id)
            self.cancel()
        self.item_map['Label'].set_text(text)
        if time > 0:
            self.to_id = GLib.timeout_add_seconds(
                time, self.cancel)

    def cancel(self):
        self.to_id = None


#Notification Class, that handles notification behavior
class Notification(Notifier):
    def __init__(self, notification):
        super().__init__(notification)
        self.item_map.get('Button').connect("clicked", self.cancel)

    def set_button_cb(signal, func):
        # Connects an additional signal callback on the cancel button
        self.item_map['Button'].connect(str(signal), func)

    def _reveal(self, type_: NotifStack):
        if self.item_map['Stack']:
            self.item_map['Stack'].set_visible_child(self.item_map[type_.value])
        self.container.set_reveal_child(True)

    def notification(self, text, time=5):
        self.notify_abstract(text, time)
        self._reveal(NotifStack.BUTTON)

    def spinner(self, text, stream_messages=False):
        self.notify_abstract(text, 0)
        self.item_map['Spinner'].start()
        self._reveal(NotifStack.SPIN)
        if stream_messages:
            return self.item_map['Label']

    def cancel(self, button=None):
        self.to_id = None
        self.container.set_reveal_child(False)
        if self.item_map['Spinner'].props.active:
            self.item_map['Spinner'].stop()

class PageNotifier(Notifier):
    def __init__(self, page):
        super().__init__(page)

    def _reveal(self, type_: NotifStack):
        self.item_map['Stack'].set_visible_child(self.item_map[type_.value])

    def spinner(self, text, stream_messages=False):
        self.notify_abstract(text, 0)
        self.item_map['Spinner'].start()
        self._reveal(NotifStack.SPIN)
        if stream_messages:
            return self.item_map['Label']

    def cancel(self, name=None):
        self.to_id = None
        self.item_map['Spinner'].stop()
        if name:
            self.item_map['Stack'].set_visible_child_name(name)

def message_dialog(win, text, ok_cb, no_cb=None, yes_no=False):
    """ Function that displays a message dialog, to the user.

    :param Gtk.Window win: Dialog parent window that it will be modal to
    :param str text: Text to display in message dialog
    :param function ok_cb: Callback for if the user selects Ok or Yes
    :param function no_cb: Optional callback for if user seelcts no, doesn't
     work if yes_no is set to False
    :param bool question: Whether to show a question message dialog, defaults
     to warning dialog if set as False.
    :param bool yes_no: Whether to show a yes and no buttons, defaults
     to ok and cancel buttons dialog if set as False.
    """
    def dialog_response(dialog, resp, ok_cb, no_cb=None):
        if resp in {Gtk.ResponseType.OK, Gtk.ResponseType.YES}:
            ok_cb()
        if resp in {Gtk.ResponseType.NO, Gtk.ResponseType.CANCEL} and no_cb:
            no_cb()
        dialog.destroy()
    message_type = Gtk.MessageType.WARNING
    buttons = Gtk.ButtonsType.OK_CANCEL
    if yes_no:
        buttons = Gtk.ButtonsType.YES_NO
    dialog = Gtk.MessageDialog(parent=win, buttons=buttons, type=message_type,
                               message_format=text, flags=Gtk.DialogFlags.MODAL)
    dialog.connect("response", dialog_response, ok_cb, no_cb)
    def show_dialog(dialog):
        dialog.show()
    # Added so it doesn't popup before it's own parent
    GLib.idle_add(show_dialog, dialog)


class Runner():
    """ Class that executes a command using the Gio.subprocess api.

    :param str root_script: Script with pkexec policy to run other scripts
    """
    def __init__(self, root_script):
        self.pkexec_approved = str(root_script)

    def exe(self, cmd: list, flag=Gio.SubprocessFlags.STDOUT_SILENCE,
                    root=False, get_output=False, error_cb=None):
        results = None
        if root:
            cmd.insert(0, self.pkexec_approved)
            cmd.insert(0, '/usr/bin/pkexec')
            suffix = ' '.join(cmd[3:])
            cmd = cmd[:3]
            cmd.append(suffix)
        process = Gio.Subprocess.new(cmd, flag)
        if get_output and flag != Gio.SubprocessFlags.STDOUT_SILENCE:
            status, results, _ = process.communicate_utf8(None, None)
        else:
            process.wait()
        if not process.get_if_exited():
            if error_cb:
                error_cb()
            print(f"Error, exit status is: {process.get_exit_status()}")
        return results
    #We want to get permission when activating the timer anyway
    def run_cmd(self, cmd: list, root=False, get_output=False, error_cb=None):
        results = None
        if root:
            cmd.insert(0, '/usr/bin/pkexec')
        process = Gio.Subprocess.new(cmd, 0)
        if get_output:
            status, results, _ = process.communicate_utf8(None, None)
        else:
            process.wait()
        if not process.get_if_exited():
            if error_cb:
                error_cb()
            print(f"Error, exit status is: {process.get_exit_status()}")
        return results

# Supplied to ListBox.set_header_func() to place separtors between rows
# https://github.com/maliciouscereal/Pithosfly/blob/master/pithos/StationsPopover.py
# https://jkangsc.blogspot.com/2015/05/how-to-add-separators-between-adiacent.html
def update_header(row, before, data=None):
    # Adds a separators to list box
    if not row.get_header() and before:
        row.set_header(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL))
    elif row.get_header():
        row.set_header(None)

def update_header_recursive(container, search_depth=3):
    """ Recursively searches a container object for Gtk.ListBoxes and sets
    the update_header function as an argument to the set_header_func method.

    :param Gtk.Container container: Container instance object
    :param int search_depth: How far should function search for objects?
    """
    def recursive_search(widget, depth):
        if hasattr(widget, 'get_children'):
            if isinstance(widget, Gtk.ListBox):
                widget.set_header_func(update_header)
            elif depth < 1:
                return
            else:
                for item in widget.get_children():
                    recursive_search(item, depth-1)
    recursive_search(container, search_depth)

def toggle_sens_btns_recur(container, value: bool, search_depth=3, vis=False):
    """ Recursively searches a container object for Gtk.Buttons and calls
    the set_sensitve method with the specified value

    :param Gtk.Container container: Container instance object
    :param bool value: Boolean value to set widget sensitivity
    :param int search_depth: How far should function search for objects?
    """
    if vis:
        def recursive_search(widget, depth):
            if hasattr(widget, 'get_children'):
                if isinstance(widget, Gtk.Button):
                    widget.set_visible(value)
                elif depth < 1:
                    return
                else:
                    for item in widget.get_children():
                        recursive_search(item, depth-1)
    else:
        def recursive_search(widget, depth):
            if hasattr(widget, 'get_children'):
                if isinstance(widget, Gtk.Button):
                    widget.set_sensitive(value)
                elif depth < 1:
                    return
                else:
                    for item in widget.get_children():
                        recursive_search(item, depth-1)
    recursive_search(container, search_depth)

# Callback to toggle the sensitive property for a widget
def toggle_sens(widget, val):
    widget.set_sensitive(val)

# DECORATOR for asynchronous operations to be paired with run_gasync_task
# using the Gio.Task api. Only keyword arguments can be passed to functions
# using the partial function from the functools module.
def gasync_task(method=False):
    def decorate(func):
        def _method(self, task, *args, **kwargs):
            res = func(self, **kwargs)
            task.return_value(res)
        def _function(task, *args, **kwargs):
            res = func(**kwargs)
            task.return_value(res)
        if method:
            return _method
        else:
            return _function
    return decorate

def run_gasync_task(func, func_cb):
    # Runs a gasync_task and callback, only keyword arguments can
    # be passed using the partial function from the functools module.
    def gasync_return(obj, pointer, callback):
        success, res = pointer.propagate_value()
        if success:
            callback(res)
    #https://discourse.gnome.org/t/how-to-return-value-in-gio-task/3455/4
    task = Gio.Task.new(None, None, gasync_return, func_cb)
    task.run_in_thread(func)

# Universal function to recieve a directory from a GtkFileChooser
# and convert to a Path object exported to a specified function callback.
def load_new_path_cb(dialog, response, function_cb=None, *args, **kwargs):
    if response == -3:
        dir_ = Path(dialog.get_filename())
        if function_cb:
            function_cb(dir_, *args, **kwargs)

def check_bin():
    # Check to see if mitmproxy and jeepney are installed
    # excluding any packages installed with pip --user
    mitmproxy = find_spec('mitmproxy')
    jeepney = find_spec('jeepney')
    installed = False
    if mitmproxy and jeepney:
        deps = [Path(mitmproxy.origin), Path(jeepney.origin)]
        for dep in deps:
            try:
                if dep.relative_to(Path('/usr')):
                    if not installed:
                        installed=True
            except ValueError as e:
                pass
    return installed
