# editor.py
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

from gi.repository import Gtk
from re import compile
from .misc import Notification


ptrn = compile(r'^$|\s')

@Gtk.Template(resource_path='/com/github/bunsenmurder/NoSurfin/ui/Editor.ui')
class ListEditor(Gtk.ApplicationWindow):
    # Set Gtype and extract some kids
    __gtype_name__ = "ListEditor"

    url_list = Gtk.Template.Child()
    url_in = Gtk.Template.Child()
    remove_btn = Gtk.Template.Child()
    add_btn = Gtk.Template.Child()
    # Passed to the Notification Class
    notif = Gtk.Template.Child()

    def __init__(self, app, dbus_proxy, name, path):
        super().__init__(application=app, title=name.title())
        self.file_path = path / f'{name}.txt'
        #self._main_window = m_win
        self._app=app
        self._dbus_proxy = dbus_proxy
        self._editor_type = None
        # Calls Notification class to handle Notifications
        self._notify = Notification(self.notif)
        if name == 'blocklist':
            self._editor_type = 0
        elif name == 'ignorelist':
            self._editor_type = 1
        # Initialize List Store
        self.listmodel = Gtk.ListStore(str)
        # Opens and stores url list in a set to ensure unique urls
        try:
            with self.file_path.open("r") as f:
                self._set = {line.rstrip() for line in f}
        #Initializes set if no file was found
        except FileNotFoundError:
                self._set = set()

        # Due to how c and gtk are, each line is stored as a list
        for line in self._set:
            self.listmodel.append([line])
        # Finishing initialization
        self.url_list.set_model(model=self.listmodel)
        self.selection = self.url_list.get_selection()

        # Call functions
        self.check_if_clock_active()
        # Connect signals
        self.connect("delete-event", self._delete)
        self._app.connect("notify::clock-active",
                                  self.check_if_clock_active)
        self.set_skip_taskbar_hint(True)

        #self.style = Gtk.CssProvider()
        # self.style.load_from_data(b'entry {border-color: Red;}')
        # self.url_in.get_style_context().remove_provider(self.style)
        #self.url_in.get_style_context().add_provider(self.style, 400)
        # self.url_in.get_style_context().add_class('keycap')
        # Class name might be box.keycap or container.keycap

    def check_if_clock_active(self, *args):
        if self._app.props.clock_active:
            self.remove_btn.props.sensitive = False
            self._dbus_proxy.create_proxy()
        else:
            self.remove_btn.props.sensitive = True
            self.add_btn.props.sensitive = True

    def save_file(self):
        with self.file_path.open("w+") as f:
            for row in self.listmodel:
                f.write(row[0])
                f.write("\n")

    def _delete(event, self, widget):
       self.save_file()

    # callback function for the "Add" button
    @Gtk.Template.Callback()
    def add_cb(self, button):
        buffer = self.url_in.get_buffer()
        rule = buffer.get_text()
        if ptrn.search(rule):
            self._notify.notification("URL cannot be empty or have spaces!")
        elif rule in self._set:
            self._notify.notification("URL already present, add a different one!")
            buffer.delete_text(0, -1)
        else:
            tree_path = self.listmodel.get_path(self.listmodel.append([rule]))
            self.url_list.scroll_to_cell(tree_path)
            self._set.add(rule)
            buffer.delete_text(0, -1)
            if self._app.props.clock_active:
                try:
                    if self._editor_type == 0:
                        self._dbus_proxy.set_block_url(rule)
                    elif self._editor_type == 1:
                        self._dbus_proxy.set_host_token(rule)
                        self.add_btn.props.sensitive = False
                except Exception as e:
                    print(f"{e}: Could not add {rule} to list!")
                    return

    @Gtk.Template.Callback()
    def remove_cb(self, button):
        # if there is still an entry in the model
        if len(self.listmodel) != 0:
            # get the selection
            (model, iter) = self.selection.get_selected()
            if iter is not None:
                self._set.remove(model[iter][0])
                self.listmodel.remove(iter)

        
