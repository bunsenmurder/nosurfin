# notify.py
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

from gi.repository import GLib, Gtk
from enum import Enum

class NotifStack(Enum):
    BUTTON = "Button"
    SPIN = "Spinner"

class Notifier():
    """ Notifier abstract class for showing notifications in front-end.
    This class assumes that the initializing container has a GtkBox as
    it's first child and a GtkLabel as one of the boxes children, with
    the other direct children of the box being unique widgets.
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


class Notification(Notifier):
    """ Notifier child class for showing drop-down notifications.

    :param Gtk.Revealer notification: GtkRevealer following the format
    specified in Notifier parent class, plus one child being a GtkStack with
    a GtkSpinner and a GtkButton as the GtkStack's children.
    """
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
    """ Notifier child class for showing  notifications within a page.

    :param Gtk.Revealer notification: GtkRevealer following the format
    specified in Notifier parent class, plus one child being a GtkStack with
    a GtkSpinner and a GtkButton as the GtkStack's children.
    """
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
    """ Function that displays a message dialog to the user.

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
