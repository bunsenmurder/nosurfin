# main.py
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

import gi, sys

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gio, GLib, Gdk
from collections import OrderedDict
from os import path
from .window import AppWindow
from .editor import ListEditor
from .sleep import CatchSleep

python_bin = sys.executable
current_dir = path.dirname(path.realpath(__file__))
pkexec_bin = '/usr/bin/pkexec'
wrapper_script = path.join(current_dir, 'nosurfin.d/systemd_wrapper.py')

class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(application_id="com.github.bunsenmurder.NoSurfin",
                         flags=Gio.ApplicationFlags.FLAGS_NONE, *args, **kwargs)
        #super().__init__(application_id="com.github.bunsenmurder.NoSurfin", *args, **kwargs)
        #GLib.set_prgname("NoSurfin")
        self._window = None
        self._editor = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.on_quit)
        self.add_action(action)

        action = Gio.SimpleAction.new("lists", None)
        action.connect("activate", self.on_lists, "blocklist")
        self.add_action(action)

        action = Gio.SimpleAction.new("ignore", None)
        action.connect("activate", self.on_lists, "ignorelist")
        self.add_action(action)

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self._window:
            self._window = AppWindow(self)
            self._window.connect("save_block", self._create_block)
            CatchSleep(self._window)
            # self._window = Window(application=self, title="NoSurfin: Time
            # to get to work")
        self._window.present()

    def _create_block(self, action, time):
        block_process = Gio.Subprocess().new([
            pkexec_bin, python_bin, wrapper_script, time], 0)
        block_process.wait()
        if block_process.get_if_exited:
            print(block_process.get_exit_status())
        self._window.check_for_block()

    def on_about(self, action, param):
        # self.about_dialog.set_program_name("NoSurfin: Time to get to work!")
        about_dialog = Gtk.AboutDialog(transient_for=self._window, modal=True)
        about_dialog.set_program_name("NoSurfin: Time to get to work!")
        about_dialog.present()

    def on_quit(self, action, param):
        self._window.destroy()

    def on_lists(self, action, param, list_name: str):
        if self._editor is not None:
            event = Gdk.Event.new(Gdk.EventType.DELETE)
            self._editor.emit("delete-event", event)
            self._editor.destroy()
        self._editor = ListEditor(self, list_name)
        self._editor.connect("destroy", self._list_destroy)
        self._editor.present()

    def _list_destroy(self, widget):
        self._editor = None


def main(version):
    app = Application()
    return app.run(sys.argv)
