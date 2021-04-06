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

import sys, os # remove this when done
from pathlib import Path
from os import path, mkdir
from gi.repository import Gtk, Gio, GLib, Gdk, GObject
from collections import OrderedDict
from .window import AppWindow
from .editor import ListEditor
from .preferences import Preferences
from .tools import Runner
from .tools.dbus import CatchSleep, UrlMgrProxy
from .tools.misc import check_bin, set_sens_btns_recur
from .notify import message_dialog
from datetime import datetime, timedelta


class Application(Gtk.Application):

    clock_active = GObject.Property(type=bool, default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(application_id="com.github.bunsenmurder.NoSurfin",
                         flags=Gio.ApplicationFlags.FLAGS_NONE, *args, **kwargs)
        #GLib.set_prgname("NoSurfin")
        self._editor = None
        self._pref_win = None
        self.window = None
        self.dbus_proxy = UrlMgrProxy()
        # Access settings using schema id
        self.settings = Gio.Settings.new('com.github.bunsenmurder.NoSurfin')

        # Path of sys.executable
        self.sys_backend = '/usr/bin/mitmdump'
        self.pipx_backend = '/opt/ns_dep/local/bin/mitmdump'

        #path_config
        # backend_bin: Could either be sys_backend or pipx_backend
        # python_bin: Python executable location
        # data: XDG_DATA_HOME/nosurfin. Where we store user data.
        # pwd: Present working directory
        # wrapper: wrapper script to connect to backend
        #
        pwd = Path(path.realpath(__file__)).parent
        self.path_cfg = {
            'backend_bin': None,
            'python_bin': sys.executable,
            'data': Path(GLib.get_user_data_dir()) / 'nosurfin',
            'pwd': pwd,
            'wrapper': pwd / 'nosurfin.d/systemd_wrapper.py',
            'sh_scripts': pwd / 'nosurfin.d/sh_scripts'
        }
        self._run = Runner(self.path_cfg['sh_scripts'] / 'run_as_root')
        # Dictionary object detailing the status of necessary components needed
        # for NoSurfin to work
        self.status ={
            'backend_set': True,
            'cert_instd': True,
            'cert_good': True,
            'cert_bad': False,
            'all_ready': True
        }
        # Checks for user data directory as specified by XDG
        if not self.path_cfg['data'].is_dir():
            self.path_cfg['data'].mkdir()

        #Define the App Style and apply it
        style = Gtk.CssProvider()
        style.load_from_resource('/com/github/bunsenmurder/NoSurfin/com.github.bunsenmurder.NoSurfin.css')
        # Gtk.StyleContext.reset_widgets(screen) for clock look
        screen = Gdk.Screen.get_default()
        ctx = Gtk.StyleContext.add_provider_for_screen(
            screen, style, 400)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        # Action name, callback, (app.action, key-accel), dataGLib.get_system_config_dirs
        menu_entries = [
            ('about', self.on_about, None, None),
            #('quit', self.on_quit, ("app.quit", ["<Ctrl>Q"]), None),
            ('lists', self.on_lists, None, "blocklist"),
            ('ignore', self.on_lists, None, "ignorelist"),
            ('prefs', self.on_settings, None, None)
        ]
        # Generate menu from list of menu entries
        # a=action, cb=callback,acc=accelerator, data=data (pass to callback)
        for a, cb, acc, data in menu_entries:
            action = Gio.SimpleAction.new(a, None)
            # Checks for data to pass to callback
            if data is not None:
                action.connect('activate', cb, data)
            else:
                action.connect('activate', cb)
            self.add_action(action)
            # Sets keyboard accelerator for an action
            if acc is not None:
                self.set_accels_for_action(*acc)

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            self.window = AppWindow(self)
            self.window.connect("save_block", self._create_block, self.path_cfg)
            CatchSleep(self, self.window)
            # self.window = Window(application=self, title="NoSurfin: Time
            # to get to work")
        self.window.present()

        stat = self.status
        sys_cert, expire = self.settings.get_value('system-cert')
        python_use = self.settings.get_enum('python-use')
        if not python_use:
            sys_backend_installed = check_bin()
            if not sys_backend_installed:
                stat['backend_set'] = False
            else:
                if Path(self.pipx_backend).exists():
                    self.settings.set_enum('python-use', 2)
                    self.path_cfg['backend_bin'] = self.pipx_backend
                else:
                    self.settings.set_enum('python-use', 1)
                    self.path_cfg['backend_bin'] = self.sys_backend
        elif python_use == 1:
            self.path_cfg['backend_bin'] = self.sys_backend
        elif python_use == 2:
            self.path_cfg['backend_bin'] = self.pipx_backend

        if sys_cert and expire:
            self.cert_expire_check(expire)
        else:
            stat['cert_instd'] = False

        if not self.props.clock_active:
            if not stat['backend_set'] or not stat['cert_instd']:
                set_sens_btns_recur(self.window.page_stack, False, vis=True)
            self.check_start_conditions_met()

    def cert_expire_check(self, expire):
        exp_dt = datetime.fromtimestamp(expire)
        week_b4_expire = exp_dt - timedelta(days=7)
        if datetime.now() > week_b4_expire:
            self.status['cert_good'] = False
            if datetime.now() > exp_dt:
                self.status['cert_bad'] = True
        else: # Resets back to defaults just in case
            self.status['cert_good'] = True
            self.status['cert_bad'] = False

    def check_start_conditions_met(self, win_modal=None, skip=0):
        stat = self.status
        if not stat['backend_set'] and skip < 1:
            def yes_cb():
                self.on_settings(None, None)
                self._pref_win.pref_stack.set_visible_child_name('advanced')
                self._pref_win.set_modal(True)
                self._pref_win.ins_dep_cb(None)
            # Skips past checks as you cannot install certs without a backend
            def no_cb():
                if self._pref_win:
                    self._pref_win.set_modal(False)
                self.check_start_conditions_met(self.window, skip=2)
            text = ("NoSurfin couldn't find mitmproxy (>5.0) and jeepney (>0.4)"
                " and cannot run without them. Would you like to install"
                " them now? If not, please install both packages through"
                " your package manager.")
            message_dialog(win_modal, text, yes_cb, no_cb, yes_no=True)
        elif not stat['cert_instd'] and skip < 1:
            def yes_cb():
                self.on_settings(None, None)
                self._pref_win.pref_stack.set_visible_child_name('advanced')
                self._pref_win.set_modal(True)
                self._pref_win.install_cert()
            def no_cb():
                if self._pref_win:
                    self._pref_win.set_modal(False)
                self.check_start_conditions_met(self.window, skip=1)
            text = ("NoSurfin's SSL certificate is not installed and cannot"
                    " run without it. Would you like to install it now? If "
                    "not, please install it using the Certificate Wizard.")
            message_dialog(win_modal, text, yes_cb, no_cb, yes_no=True)
        elif not stat['cert_good'] and skip < 2:
            def yes_cb():
                self.status['cert_good'] = True
                self.status['cert_bad'] = False
                self.on_settings(None, None)
                self._pref_win.set_modal(True)
                self._pref_win.reinstall_certs()
                self._pref_win.pref_stack.set_visible_child_name('advanced')
            def no_cb():
                if self._pref_win:
                    self._pref_win.set_modal(False)
                self.check_start_conditions_met(self.window, skip=2)
            _, expire = self.settings.get_value('system-cert')
            exp_dt = datetime.fromtimestamp(expire)
            exp = f"The NoSurfin SSL certificate will expire on: {exp_dt} \n"
            if stat['cert_bad']:
                exp = ("NoSurfin's SSL certificate has expired and cannot "
                        "run without it.")
                set_sens_btns_recur(self.window.page_stack, False, vis=True)
            text = (" Would you like to reinstall it now? If not, please install"
                    " it before the expiration with the Certificate Wizard.")
            text = exp + text
            message_dialog(None, text, yes_cb, no_cb, yes_no=True)
        if stat['backend_set'] & stat['cert_instd'] and not stat['cert_bad']:
            set_sens_btns_recur(self.window.page_stack, True, vis=True)
            if self._pref_win:
                self._pref_win.destroy()


    def on_about(self, action, param):
        #self.about_dialog.set_program_name("NoSurfin: Time to get to work!")
        about_dialog = Gtk.AboutDialog(transient_for=self.window, modal=True)
        about_dialog.set_program_name("NoSurfin: Take back your productivity!")
        about_dialog.present()

    def on_quit(self, action, param):
        self._save_list_destroy()
        self._pref_win.destroy()
        self.window.destroy()

    def on_lists(self, action, param, list_name: str):
        def set_none_cb(widget):
            self._editor = None
        self._save_list_destroy()
        self._editor = ListEditor(self, self.dbus_proxy,
                                    list_name, self.path_cfg['data'])
        self._editor.connect("destroy", set_none_cb)
        self._editor.present()

    def _save_list_destroy(self):
        if self._editor is not None:
            event = Gdk.Event.new(Gdk.EventType.DELETE)
            self._editor.emit("delete-event", event)
            self._editor.destroy()

    def on_settings(self, action, param, show=True):
        def set_none_cb(widget):
            self._pref_win = None
        if not self._pref_win:
            self._pref_win = Preferences(self)
            self._pref_win.connect("destroy", set_none_cb)
        if show:
            self._pref_win.present()


    def _create_block(self, action, time, cfg):
        self._run.run_cmd([cfg['python_bin'], str(cfg['wrapper']), time,
                        str(cfg['data']), cfg['backend_bin']], True)
        self.window.check_for_block()


def main(version):
    app = Application()
    return app.run(sys.argv)
