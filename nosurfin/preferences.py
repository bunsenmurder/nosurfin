# preferences.py
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

from gi.repository import Gtk, GObject, Gio
from .wizard import CertWizard
from .misc import (Notification, Runner, update_header_recursive, check_bin,
load_new_path_cb, toggle_sens_btns_recur, message_dialog, gasync_task, run_gasync_task)
from pathlib import Path
from shutil import copy2, move
from datetime import datetime as dt
from functools import partial

import os


@Gtk.Template(resource_path="/com/github/bunsenmurder/NoSurfin/ui/Preferences.ui")
class Preferences(Gtk.ApplicationWindow):
    # Set GObject things and retrieve so template objects
    __gtype_name__ = "PrefWindow"

    # Main Stack Page
    pref_stack = Gtk.Template.Child()
    # Passed to the Notification Class
    notif = Gtk.Template.Child()
    # Drop-down boxes
    filter_drop_down = Gtk.Template.Child()
    theme_drop_down = Gtk.Template.Child()

    # Wizard button
    start_wiz_btn = Gtk.Template.Child()

    # Advanced button size group
    adv_btn_size_group = Gtk.Template.Child()

    # Pipx dependancies installer
    install_dep_row = Gtk.Template.Child()
    remove_dep_row = Gtk.Template.Child()


    def __init__(self, app):
        super().__init__()
        """Initialize Application Window

        :param Gtk.Application app: Application instance object
        """
        self.settings = app.settings
        self.path_cfg = app.path_cfg
        self._app = app
        self.data_dir = self.path_cfg['data']
        self.dep_man_script = self.path_cfg['sh_scripts'] / 'pipx_dep_man'
        self.cleaner_script = self.path_cfg['sh_scripts'] / 'cleaner.sh'
        self._run = Runner(self.path_cfg['sh_scripts'] / 'run_as_root')

        self._notify = Notification(self.notif)
        self._wiz = None

        # Recursively searches self for ListBoxes and set separators
        update_header_recursive(self.pref_stack, search_depth=6)

        ## Build drop-down menus
        #Get all possible enums for keys and store in GtkListStores
        list_store = self.filter_drop_down.get_model()
        theme_list_store = self.theme_drop_down.get_model()
        for item in self.settings.get_range('filter-mode')[1]:
            list_store.append([item])
        for item in self.settings.get_range('clock-face')[1]:
            theme_list_store.append([item])
        self.filter_drop_down.set_active(app.settings.get_enum('filter-mode'))
        self.theme_drop_down.set_active(app.settings.get_enum('clock-face'))
        # Define callbacks for drop-downs
        def setting_changed(settings_obj, key, obj):
            new_val = settings_obj.get_enum(str(key))
            if obj.get_active() != new_val:
                obj.set_active(new_val)

        def combo_changed(combo_box, key):
            self.settings.set_enum(key, combo_box.get_active())

        self.settings.connect("changed::filter-mode", setting_changed,
                                                        self.filter_drop_down)
        self.settings.connect("changed::clock-face", setting_changed,
                                                        self.theme_drop_down)
        #Set settings value if selection has changed
        self.filter_drop_down.connect("changed", combo_changed, 'filter-mode')
        self.theme_drop_down.connect("changed", combo_changed, 'clock-face')

        self._check_if_clock_active()
        self._check_pipx()
        self._app.connect("notify::clock-active", self._check_if_clock_active)
        #print(self.path_cfg['pwd'])


    def _check_pipx(self):
        python_use = self.settings.get_enum('python-use')
        wiz_btn_row = self.start_wiz_btn.get_parent().get_parent()
        if python_use == 0:
            if not self.install_dep_row.get_visible():
                self.install_dep_row.set_visible(True)
            if self.remove_dep_row.get_visible():
                self.remove_dep_row.set_visible(False)
            if not self._app.status['backend_set']:
                wiz_btn_row.set_visible(False)
        elif python_use == 2:
            if not self.remove_dep_row.get_visible():
                self.remove_dep_row.set_visible(True)
            if self.install_dep_row.get_visible():
                self.install_dep_row.set_visible(False)
            if not wiz_btn_row.get_visible():
                wiz_btn_row.set_visible(True)
        else:
            self.install_dep_row.set_visible(False)
            self.remove_dep_row.set_visible(False)
            if not wiz_btn_row.get_visible():
                wiz_btn_row.set_visible(True)

    def _check_if_clock_active(self, *args):
        if self._app.props.clock_active:
            #self.adv_btn_size_group.set_sensitive(False)
            for child in self.adv_btn_size_group.get_widgets():
                child.set_sensitive(False)
            self.start_wiz_btn.set_sensitive(True)
            if not self._wiz:
                self.wiz_cb(None, False)
            self._wiz.set_system_certs_sens(False)
        else:
            for child in self.adv_btn_size_group.get_widgets():
                child.set_sensitive(True)
            if self._wiz:
                self._wiz.set_system_certs_sens(True)

    def install_cert(self, val=None, *args):
        def check_sys_status_cb(*args):
            def finish_cb(*args):
                self._notify.notification("Done")
                self._app.check_start_conditions_met()
                toggle_sens_btns_recur(self, True, search_depth=11)
            sys_cert, expire = self.settings.get_value('system-cert')
            if sys_cert and expire:
                self._app.status['cert_instd'] = True
                self._app.cert_expire_check(expire)
                self._wiz.reinstall_removed_certs(finish_cb)
            else:
                self._notify.notification("Error: Could not install certificate")
                toggle_sens_btns_recur(self, True, search_depth=11)
            # Ensures Wizard is set back to default screen
            #self._wiz.route_cb(self._wiz.menu)
        toggle_sens_btns_recur(self, False, search_depth=11)
        self.wiz_cb(None, show=False)
        self._notify.spinner("Installing...")
        self._wiz.install_sys_certs(check_sys_status_cb)

    @gasync_task(method=True)
    def _run_cleaner_script(self):
        flag=Gio.SubprocessFlags.STDERR_MERGE
        cmd=[str(self.cleaner_script), str(self.data_dir), str(self.path_cfg['pwd'])]
        output = self._run.exe(cmd, root=True, get_output=True, flag=flag)


    @gasync_task(method=True)
    def _run_dep_man(self, install=True):
        flags=Gio.SubprocessFlags.STDOUT_PIPE|Gio.SubprocessFlags.STDERR_SILENCE
        installed=False
        cmd1=[str(self.dep_man_script), '-r']
        if install:
            cmd1=[str(self.dep_man_script), '-i']
        cmd2=[str(self.dep_man_script), '-v']
        self._run.exe(cmd1, root=True,flag=flags)
        output = self._run.exe(cmd2, root=True, get_output=True, flag=flags)
        if output.strip() == "installed":
            installed=True
        return installed

    @Gtk.Template.Callback()
    def ins_dep_cb(self, button):
        def finish_cb(res, *args):
            if res:
                self.settings.set_enum('python-use', 2)
                if not self._app.status['backend_set']:
                    self._app.status['backend_set'] = True
                    self.path_cfg['backend_bin'] = self._app.pipx_backend
                    self._app.check_start_conditions_met(self)
                self._check_pipx()
            toggle_sens_btns_recur(self, True, search_depth=11)
            self._notify.notification("Done")
        toggle_sens_btns_recur(self, False, search_depth=11)
        self._notify.spinner("Installing")
        run_gasync_task(self._run_dep_man, finish_cb)

    @Gtk.Template.Callback()
    def rmv_dep_cb(self, button):
        def finish_cb(res, *args):
            if not res:
                if check_bin():
                    self.settings.set_enum('python-use', 1)
                    self.path_cfg['backend_bin'] = self._app.sys_backend
                    self._app.check_start_conditions_met(self)
                else:
                    self.settings.set_enum('python-use', 0)
                    self.path_cfg['backend_bin'] = None
                self._check_pipx()
            toggle_sens_btns_recur(self, True, search_depth=11)
            self._notify.notification("Done")
        toggle_sens_btns_recur(self, False, search_depth=11)
        self._notify.spinner("Removing")
        par_func = partial(self._run_dep_man, install=False)
        run_gasync_task(par_func, finish_cb)

    @Gtk.Template.Callback()
    def wiz_cb(self, obj, show=True):
        def set_none_cb(widget):
            self._wiz = None
        if self._wiz is None:
            self._wiz = CertWizard(self.path_cfg, self.settings)
            self._wiz.connect("destroy", set_none_cb)
            self._wiz.set_transient_for(self)
        if show:
            self._wiz.present()
            if not self._app.status['cert_instd']:
                def call_app_check(val, *args):
                    _, cert_expire = self.settings.get_value('system-cert')
                    if cert_expire > 0:
                        self._app.status['cert_instd'] = True
                        self._app.check_start_conditions_met(self, skip=2)
                self._wiz.connect("certs_installed", call_app_check)

    @Gtk.Template.Callback()
    def factory_reset_cb(self, obj):
        message = ("This action is irreversible and will completly reset "
        "NoSurfin and remove all application data. Do you wish to continue?")
        message_dialog(self, message, self._delete_all_certs, yes_no=True)

    def reinstall_certs(self):
        self._delete_all_certs(factory_reset=False)

    def _delete_all_certs(self, obj=None, factory_reset=True):
        lab = self._notify.spinner("Working...", stream_messages=True)
        toggle_sens_btns_recur(self, False, search_depth=11)
        self.wiz_cb(None, show=False)
        if factory_reset:
            def cleaner_cb(*args):
                def finish_cb(*args):
                    toggle_sens_btns_recur(self, True, search_depth=11)
                    self._notify.cancel()
                    self.settings.reset('added-dirs')
                    self.settings.reset('banned-dirs')
                    self.settings.reset('system-cert')
                    self.settings.reset('xdg-user-dirs')
                    self.settings.reset('python-use')
                    self.settings.reset('clock-face')
                    self.settings.reset('xdg-user-dirs')
                    self.settings.reset('filter-mode')
                    # Add command to do a timer before quitting
                    self._app.quit()
                run_gasync_task(self._run_cleaner_script, finish_cb)
            self._wiz.connect("certs_delete_done", cleaner_cb)
        else:
            self._wiz.connect("certs_delete_done", self.install_cert)
        self._wiz.delete_all_certs()

    @Gtk.Template.Callback()
    def export_list_cb(self, button):
        def export_list(path):
            blocklist = self.data_dir / 'blocklist.txt'
            ignorelist = self.data_dir / 'ignorelist.txt'
            time_ = dt.now().strftime("%m%d%y_%H%M%S-")
            if os.access(str(path), os.W_OK):
                if blocklist.exists():
                    blocklist_new = path / f'{time_}blocklist.txt'
                    copy2(str(blocklist), str(blocklist_new))
                else:
                    print("Block list file doesn't exist.")
                if ignorelist.exists():
                    ignorelist_new = path / f'{time_}ignorelist.txt'
                    copy2(str(ignorelist), str(ignorelist_new))
                else:
                    print("Ignore list file doesn't exist.")
                self._notify.notification(f"Exported lists to {path}")
            else:
                self._notify.notification(f"Cannot export to {path} don't have write permissions.")

        self.open_dir(export_list, text="Select a Folder to Export to")
    # TODO: Add an option for recovery of old list files.
    @Gtk.Template.Callback()
    def import_list_cb(self, button):
        def import_list(path):
            blocklist = self.data_dir / 'blocklist.txt'
            try:
                if blocklist.exists():
                    blocklist_old = self.data_dir/f'blocklist_bak.txt'
                    print(f"Detected previous blocklist.txt"
                    f", saving as {blocklist_old}")
                    move(str(blocklist), str(blocklist_old))
                copy2(str(path) , str(blocklist))
                self._notify.notification(f"Successfully imported {path.name}")
            except Exception as e:
                self._notify.notification(f"Error: {e}")

        self.open_dir(import_list, text="Select a File to Import", export=False)

    @Gtk.Template.Callback()
    def import_ign_list_cb(self, button):
        def import_list(path):
            ignorelist = self.data_dir / 'ignorelist.txt'
            try:
                if ignorelist.exists():
                    ignorelist_old = self.data_dir/f'ignorelist_bak.txt'
                    print(f"Detected previous ignorelist.txt"
                    f", saving as {ignorelist_old}")
                    move(str(ignorelist), str(ignorelist_old))
                copy2(str(path) , str(ignorelist))
                self._notify.notification(f"Successfully imported {path.name}")
            except Exception as e:
                self._notify.notification(f"Error: {e}")

        self.open_dir(import_list, text="Select a File to Import", export=False)

    def open_dir(self, cb, text, export=True):
        acc_lab=None
        action = Gtk.FileChooserAction.SELECT_FOLDER
        if not export:
            acc_lab="Import"
            action = Gtk.FileChooserAction.OPEN

        file_dialog = Gtk.FileChooserNative.new(text, self, action, acc_lab)
        if not export:
            filter_ = Gtk.FileFilter.new()
            filter_.set_name("Text Files")
            filter_.add_pattern("*.txt")
            file_dialog.set_filter(filter_)
        file_dialog.connect("response", load_new_path_cb, cb)
        file_dialog.run()
