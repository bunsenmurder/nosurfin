# window.py
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

import os
from gi.repository import Gtk, GLib
from re import compile

ptrn = compile(r'^$|\s')

@Gtk.Template(resource_path='/com/github/bunsenmurder/NoSurfin/Editor.ui')
class ListEditor(Gtk.ApplicationWindow):
    # Set Gtype and extract some kids
    __gtype_name__ = "ListEditor"

    url_list = Gtk.Template.Child()
    url_in = Gtk.Template.Child()

    def __init__(self, app, name):
        super().__init__(application=app, title=name)
        self.error = False
        # Check for data dir as specified by XDG
        xdg_data_dir = os.path.join(GLib.get_user_data_dir(), 'nosurfin')
        if not os.path.isdir(xdg_data_dir):
            os.mkdir(xdg_data_dir)
        self.file_path = os.path.join(xdg_data_dir, f'{name}.txt')

        # Initialize CSS and List Store
        self.style = Gtk.CssProvider()
        self.listmodel = Gtk.ListStore(str)
        self.style.load_from_data(b'entry {border-color: Red;}')

        # Opens and stores url list in a set to ensure unique urls
        try:
            with open(self.file_path, "r") as f:
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
        self.connect("delete-event", self._delete)


    def save_file(self):
        with open(self.file_path, "w+") as f:
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
        # Remove error if it appeared before
        if self.error == True:
            self.url_in.get_style_context().remove_provider(self.style)
            self.error = False
        # TODO: Emit notification for any errors
        if ptrn.search(rule):
            print("Cannot be empty or have spaces! Try Again.")
            self.url_in.get_style_context().add_provider(self.style, 400)
            self.error = True
        elif rule in self._set:
            print("URL already present, add a different one!")
            buffer.delete_text(0, -1)
        else:
            tree_path = self.listmodel.get_path(self.listmodel.append([rule]))
            self.url_list.scroll_to_cell(tree_path)
            self._set.add(rule)
            buffer.delete_text(0, -1)

    @Gtk.Template.Callback()
    def remove_cb(self, button):
        # if there is still an entry in the model
        if len(self.listmodel) != 0:
            # get the selection
            (model, iter) = self.selection.get_selected()
            if iter is not None:
                print(f"{model[iter][0]} has been removed")
                self._set.remove(model[iter][0])
                self.listmodel.remove(iter)

