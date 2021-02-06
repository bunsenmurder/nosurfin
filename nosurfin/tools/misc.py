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

from gi.repository import Gtk, Gio
from pathlib import Path
from importlib.util import find_spec

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
    """ Function to be supplied to the set_header_func method of a GtkListBox.
    This function adds seperators between the GtkListBox's rows.
    """
    # Adds a separators to list box
    if not row.get_header() and before:
        row.set_header(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL))
    elif row.get_header():
        row.set_header(None)

def update_header_recur(container, search_depth=3):
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
#toggle_sens_btns_recur
def set_sens_btns_recur(container, val: bool, search_depth=3, vis=False):
    """ Recursively searches a container object for Gtk.Buttons and sets the
     widget sensitive or visibility property to the specified value.

    :param Gtk.Container container: Container instance object
    :param bool val: Boolean value to set widget sensitivity/visibility
    :param int search_depth: How far should function search for objects?
    """
    if vis:
        def recursive_search(widget, depth):
            if hasattr(widget, 'get_children'):
                if isinstance(widget, Gtk.Button):
                    widget.set_visible(val) # Changes visibility
                elif depth < 1:
                    return
                else:
                    for item in widget.get_children():
                        recursive_search(item, depth-1)
    else:
        def recursive_search(widget, depth):
            if hasattr(widget, 'get_children'):
                if isinstance(widget, Gtk.Button):
                    widget.set_sensitive(val) #Changes sensitivity
                elif depth < 1:
                    return
                else:
                    for item in widget.get_children():
                        recursive_search(item, depth-1)
    recursive_search(container, search_depth)

def set_sens(widget, val):
    """ Function that sets widget sensitivity property to the specified value.
    Used mainly with the Gtk.Container.foreach method.

    :param bool val: Boolean value to set widget sensitivity
    """
    widget.set_sensitive(val)

def check_bin():
    """ Function that checks if mitmproxy and jeepney are installed, excluding
    any packages installed with pip --user.
    """
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
