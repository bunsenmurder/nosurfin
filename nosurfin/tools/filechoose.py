# filechoose.py
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
from pathlib import Path

# Add to filechooser handler class
def check_path_invalid(p):
    """ Notifier child class for showing  notifications within a page.

    :param Gtk.Revealer notification: GtkRevealer following the format
    specified in Notifier parent class, plus one child being a GtkStack with
    a GtkSpinner and a GtkButton as the GtkStack's children.
    """
    return p.is_socket()|p.is_fifo()|p.is_block_device()|p.is_char_device()

# Universal function to recieve a directory from a GtkFileChooser
# and convert to a Path object exported to a specified function callback.
def load_new_path(dialog, response, func_cb=None, *args, **kwargs):
    if response == -3:
        dir_ = Path(dialog.get_filename())
        if func_cb:
            func_cb(dir_, *args, **kwargs)

def open_dir(text, func_cb, acpt_lab=None, can_lab=None, openf=False,
            return_obj=False):
    action = Gtk.FileChooserAction.SELECT_FOLDER
    if openf:
        action = Gtk.FileChooserAction.OPEN
    file_dia = Gtk.FileChooserNative.new(text, None, action, acpt_lab, can_lab)
    file_dia.connect("response", load_new_path, func_cb)
    if return_obj:
        # Used if modifying file chooser object
        return file_dia
    else:
        file_dia.run()


