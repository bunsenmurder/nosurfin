# wizard.py
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
from .dbus_tools import ProxyFactorySync
from .misc import (Notification, PageNotifier, Runner, load_new_path_cb,
update_header, toggle_sens, gasync_task, run_gasync_task, message_dialog, toggle_sens_btns_recur)
from enum import Enum
from shutil import copy2
from pathlib import Path
from os.path import exists
from functools import partial
from datetime import datetime as dt

import pickle as pk
import os

def check_p11k():
    # Checks if p11-kit is installed and activated, and outputs the appropriate
    # command to execute for installing the mitmproxy certificate.
    proxy = ProxyFactorySync("org.freedesktop.systemd1",
                                "/org/freedesktop/systemd1",
                                "org.freedesktop.systemd1.Manager")
    p11k_state = False
    try:
        p11k_obj_path = proxy.GetUnit('(s)', 'p11-kit-server.socket')
        proxy = ProxyFactorySync("org.freedesktop.systemd1", p11k_obj_path,
                                 "org.freedesktop.DBus.Properties")
        p11k_state = proxy.Get('(ss)',"org.freedesktop.systemd1.Unit", 'UnitFileState')
    except Exception as e:
        print(e)
        pass

    if p11k_state == "enabled":
        return 'p11k'
    else:
        return 'etc_ssl_certs'

def check_path_invalid(p):
    return p.is_socket()|p.is_fifo()|p.is_block_device()|p.is_char_device()

def open_dir(text, func_cb):
    file_dialog = Gtk.FileChooserNative.new(
        text, None, Gtk.FileChooserAction.SELECT_FOLDER
    )
    file_dialog.connect("response", load_new_path_cb, func_cb)
    file_dialog.run()

class Action(Enum):
    NONE = 0
    VERIFY = 1
    INSTALL = 2
    REMOV = 3
    INSTALL_SYS = 4
    CHECK = 5
    RECOVER = 6


@Gtk.Template(resource_path="/com/github/bunsenmurder/NoSurfin/ui/ListBoxRow.ui")
class ListBoxRow(Gtk.ListBoxRow):
    # Cert Wizard list box row template
    __gtype_name__ = "ListBoxRow"

    checkbox = Gtk.Template.Child()
    prime_lab = Gtk.Template.Child()
    second_lab = Gtk.Template.Child()

    def __init__(self, label1, label2):
        super().__init__()
        self.prime_lab.set_text(label1)
        self.second_lab.set_text(label2)
        self.path = None


@Gtk.Template(resource_path="/com/github/bunsenmurder/NoSurfin/ui/CertWizard.ui")
class CertWizard(Gtk.ApplicationWindow):
    # Set GObject things and retrieve so template objects
    __gtype_name__ = "CertWiz"
    # Emitted after NoSurfins certificate has been removed from all cert stores.
    __gsignals__ = {
        'certs_delete_done': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
        'certs_installed': (GObject.SignalFlags.RUN_LAST, None, (bool,))
    } # Can emit success, error
    ## Main Body and Header Bar Stacks
    main_stack = Gtk.Template.Child()
    header_stack = Gtk.Template.Child()
    ##

    ## Widgets to map
    # Menu List Box Children, 1st Page
    sys_certs_install = Gtk.Template.Child()
    certs_install = Gtk.Template.Child()
    certs_remove = Gtk.Template.Child()
    certs_next_btn = Gtk.Template.Child() # Next button, 2nd Page
    menu = Gtk.Template.Child() # Menu button, 3rd Page

    ## Misc
    # Select Certs Page(2nd) Widgets
    select_certs_lab = Gtk.Template.Child()
    select_certs_lb = Gtk.Template.Child() # Select certs listbox
    select_certs_scroll = Gtk.Template.Child()
    select_all_chck = Gtk.Template.Child()
    action_box = Gtk.Template.Child()
    # Passed to the Notification Class
    notif = Gtk.Template.Child()

    # Certificate nickname stored in cert databases and bundles
    cert_nname = "NsMitmProxy"

    def __init__(self, path_cfg, settings):
        super().__init__()
        """Initialize Application Window

        :param Dict path_cfg: configuration of file paths
        """
        ## Setting Init args to self
        self.settings = settings
        # Paths
        self.cert_file_name = 'mitmproxy-ca-cert_ns.pem'
        self.data_dir = path_cfg['data']
        self.cert_path = self.data_dir / self.cert_file_name
        self.sys_script = path_cfg['sh_scripts'] / 'cert_util_sys'
        self.pem_script = path_cfg['sh_scripts'] / 'cert_util_pem'
        self._run = Runner( path_cfg['sh_scripts']/'run_as_root' )

        # Init Notification Objects
        self._notify = Notification(self.notif)
        self._process = PageNotifier(self.main_stack.get_child_by_name('process'))

        # CertWizard Class State Properties
        self._indexer_ran = False
        self._prev_action = None
        self._error_buffer = None
        self._all_delete_activated = False
        self.show_system_cert = True

        ## Data Structures
        #self._system_cert = {}
        self._f_index = {}
        self._selected_certs = []
        # Maps the id of the routing widget to the appropriate stack name pairs
        self.stack_map = {
            self.sys_certs_install:
                {'main': 'process', 'head': 'menu_close',
                'trans': 3, 'action': Action.INSTALL_SYS},
            self.certs_install:
                {'main': 'select_certs', 'head': 'back_next',
                'trans': 3, 'action': Action.INSTALL},
            self.certs_remove:
                {'main': 'select_certs', 'head': 'back_next',
                'trans': 3, 'action': Action.REMOV},
            self.certs_next_btn:
                {'main': 'process', 'head': 'menu_close',
                'trans': 3 , 'action': Action.CHECK},
            self.menu:
                {'main': 'menu', 'head': 'cancel_smenu',
                'trans': 2, 'action': Action.NONE}

        }

        ## Initialization Method Calls
        # Sets seperators for main page list box
        self.sys_certs_install.get_parent().set_header_func(update_header)
        # Loads index pickle if it exists
        try:
            self._f_index = pk.load(open(self.data_dir/'cert_index.pkl','rb'))
        except FileNotFoundError:
            pass

        ## Connect Signals
        self.select_all_chck.connect('toggled', self.select_all_cb)

        #if self.get_visible():
        #    self._validate_cert()

        self.connect_after('show', self._validate_cert)
        ## Add logic to disable the bottom two list boxes if system cert is
        # not installed

    ## Public Class Methods
    def delete_all_certs(self, lab=None):
        def remove_all_cb(obj=None, lab=None):
            def finish_cb(obj=None, lab=None):
                if lab:
                    lab.set_text("All certs have been deleted.")
                self.emit('certs_delete_done', True)
            self._error_buffer = None
            self._all_delete_activated = True
            self._update_listbox(None, installed=True)
            self.select_all_chck.set_active(True)
            self._prev_action = Action.REMOV
            par_func_cb = partial(finish_cb, lab=lab)
            self.route_cb(lb=self.certs_next_btn, data=par_func_cb)

        par_func_cb = remove_all_cb
        if lab:
            lab.set_text("Working...")
            par_func_cb = partial(remove_all_cb, lab=lab)
        run_gasync_task(self._find_certs, par_func_cb)

    def reinstall_removed_certs(self, func_cb):
        if self._selected_certs:
            self._prev_action = Action.INSTALL
            self.route_cb(lb=self.certs_next_btn, data=func_cb)
        else:
            func_cb()

    def install_sys_certs(self, func_cb):
        self.route_cb(lb=self.sys_certs_install, data=func_cb)

    def set_system_certs_sens(self, val: bool):
        self.sys_certs_install.set_sensitive(val)
        self.show_system_cert = val
        if self._indexer_ran:
            lb_kids = self.select_certs_lb.get_children()
            if len(lb_kids) > 0 and self._prev_action == Action.REMOV:
                lb_kids[0].set_sensitive(val)


    def _load_certificate(self):
        success = False
        self.cert_binary_format = None
        try:
            cert_path = None
            with self.cert_path.open('rb') as cert:
                self.cert_binary_format = cert.read()
            success = True
        except FileNotFoundError as e:
            pass
        return success

    def _validate_cert(self, *args):
        file_key, cert_expire = self.settings.get_value('system-cert')
        if not self.cert_path.exists() and file_key and cert_expire > 0:
            def recovery_cb(*args):
                def finish_cb(val):
                    if val:
                        self._notify.notification("Done.")
                    else:
                        self._notify.notification("Error: Could not recover certificate.")
                self._notify.notification("Attempting Recovery...")
                run_gasync_task(self._recover_cert, finish_cb)

            text = ("Could not find the System Certificate in user data "
            "directory. Attempting to recover.")
            message_dialog(self, text, recovery_cb, self.close_cb)

    @gasync_task(method=True)
    def _recover_cert(self):
        # Copy2 doesn't work from root, remove and rely on script only
        success = True
        flags=Gio.SubprocessFlags.STDOUT_PIPE|Gio.SubprocessFlags.STDERR_MERGE
        self._check_sys_cert_status()
        file_key, cert_expire = self.settings.get_value('system-cert')
        if file_key and cert_expire > 0:
            cmd = self._cert_cmd_factory(file_key, Action.RECOVER, dir_='-z')
            output = self._run.exe(cmd, root=True, get_output=True, flag=flags)
        else:
            success = False

        return success

    ## Utility functions
    def _dump_pickle(self):
        # Saves file index to a pickle
        pk.dump(self._f_index, open(self.data_dir/'cert_index.pkl', 'wb'))

    def _error_notify(self):
        if self._error_buffer:
            self._notify.notification(f"Error: {self._error_buffer}", time=0)
            self._error_buffer = None

    def _cert_cmd_factory(self, file_key, action: Action, dir_=None):
        if dir_ == None:
            dir_ = Path().home()
        base_cmds = {
            'cert9.db': {
                'type': 'nss',
                'base': ['certutil', '-d', f'{str(dir_)}', '-n', self.cert_nname],
            },
            #Chromes cert key is concatenated parent dir and file
            'nssdb/cert9.db': {
                'type': 'nss',
                'base': ['certutil', '-d', f'sql:{dir_}', '-n', self.cert_nname]
            },
            'etc_ssl_certs': {
                'type': 'system',
                'base': [str(self.sys_script), '-c', dir_]
            },
            'p11k': {
                'type': 'system',
                'base': [str(self.sys_script), '-p', dir_]
            },# Virtual env config, search using pyvenv.cfg, #cacert.pem for python
            #https://stackoverflow.com/questions/5215771/how-can-i-check-if-the-certificate-file-i-have-is-in-pem-format
            '.pem': {
                'type': 'x509_ASCII',
                'base': [str(self.pem_script), f'-n={self.cert_nname}',
                            f'-s={self.cert_path}',
                            f'-d={dir_}']
            }
                         }
        cmd_suffixes = {
            'system': {
                'VERIFY': ['-v'],
                'INSTALL_SYS': ['-i', '-v', f'-d={self.data_dir}'],
                'REMOV': ['-r'],
                'RECOVER': ['-s', f'-d={self.data_dir}']
            },
            'nss': {
                'VERIFY': ['-V', '-u', 'L'],
                'INSTALL': ['-A', '-t', 'C,', '-i', str(self.cert_path)],
                'REMOV': ['-D']
            },
            'x509_ASCII': {
                'VERIFY': ['-v'],
                'INSTALL': ['-i'],
                'REMOV': ['-r']
            }
                        }
        file = base_cmds[file_key]
        return file['base'] + cmd_suffixes.get(file['type'])[action.name]

    def _check_sys_cert_status(self, hard_check=False):
        flags=Gio.SubprocessFlags.STDOUT_PIPE|Gio.SubprocessFlags.STDERR_SILENCE
        file_key, cert_expire = self.settings.get_value('system-cert')
        if self.settings.get_enum('python-use') == 2:
            last_arg = '-x'
        else: #z for zero, as it is just a dummy var that will not be parsed
            last_arg = '-z'

        if file_key and cert_expire > 0:
            if hard_check:
                file_key = check_p11k()
            cmd = self._cert_cmd_factory(file_key, Action.VERIFY, last_arg)
            check_status = self._run.exe(cmd, get_output=True, flag=flags)
        else:
            file_key = check_p11k()
            cmd = self._cert_cmd_factory(file_key, Action.VERIFY, last_arg)
            check_status = self._run.exe(cmd, get_output=True, flag=flags)
        # In case the check has alread been done
        out = check_status.strip().split(': ')
        if out[-1] == 'certificate is valid':
            if cert_expire != int(out[0]): # s=
                entry = GLib.Variant('(sx)', (file_key, int(out[0])))
                self.settings.set_value('system-cert', entry)
        else:
            entry = GLib.Variant('(sx)', (file_key, 0))
            self.settings.set_value('system-cert', entry)

    def _check_cert_status(self, db, file_key):
        flags=Gio.SubprocessFlags.STDOUT_PIPE|Gio.SubprocessFlags.STDERR_SILENCE
        cmd = self._cert_cmd_factory(file_key, Action.VERIFY, db.parent)
        check_status = self._run.exe(cmd, get_output=True, flag=flags)
        self._f_index[db] = {'db_name': file_key, 'installed': False}
        dict_entry = self._f_index[db] # Save to prevent constant lookups
        if check_status.strip().split(': ')[-1] == 'certificate is valid':
            dict_entry['installed'] = True

    def _check_pem_status(self, db, file_key):
        flags=Gio.SubprocessFlags.STDOUT_PIPE|Gio.SubprocessFlags.STDERR_SILENCE
        cmd = self._cert_cmd_factory(file_key, Action.VERIFY, db)
        check_status = self._run.exe(cmd, get_output=True, flag=flags)
        output = check_status.strip().split(': ')[-1]
        if output != 'certificate is not correct type':
            self._f_index[db] = {'db_name': file_key, 'installed': False,
                                'modtime': 0}
            dict_entry = self._f_index[db] # Save to prevent constant lookups
            if output == 'certificate is valid':
                dict_entry['installed'] = True
                dict_entry['modtime'] = db.stat().st_mtime


    def _delete_lb_children(self):
        # Destroys any children in select certs listbox
        children = self.select_certs_lb.get_children()
        if children:
            for child in children:
                child.destroy()

    def _inst_sys_certs(self, action, file_key):
        if self.settings.get_enum('python-use') == 2:
            last_arg = '-x'
        else: #z for zero, as it is just a dummy var that will not be parsed
            last_arg = '-z'
        cmd = self._cert_cmd_factory(file_key, action, last_arg)
        self._run.exe(cmd, root=True)
        self._check_sys_cert_status()

    # Gasync finishing cb, requires setting obj as None to hold null return
    def _update_listbox(self, obj=None, installed=False):
        self._delete_lb_children()
        # Resets the scrollbar positions
        self.select_certs_scroll.get_vadjustment().set_value(0)
        self.select_certs_scroll.get_hadjustment().set_value(0)


        def insert_row(row, pos=-1):
            row.checkbox.connect_after("button-release-event", self.selected_cb)
            self.select_certs_lb.insert(row, pos)
        file_key, cert_expire = self.settings.get_value('system-cert')
        if self.show_system_cert:
            def del_sys(cb, *args):
                def yes_cb():
                    pass
                def no_cb():
                    cb.set_active(False)
                    self.selected_cb()
                text = \
                    ("The System Certificate and all currently installed "
                    " certificates will need be reinstalled next time you "
                    " open NoSurfin. Do you still wish to uninstall the"
                    " System Certificate?")
                if cb.get_active():
                    message_dialog(self, text, yes_cb, no_cb, yes_no=True)

            if cert_expire > 0 and installed:
                date_expire = dt.fromtimestamp(cert_expire).strftime('%Y-%m-%d')
                expire_lab = f"Expires: {date_expire}"
                primary_label = "System Certificate"
                if file_key == 'p11k':
                    primary_label = primary_label + " (p11-kit)"
                row = ListBoxRow(primary_label, expire_lab)
                if not self._all_delete_activated:
                    row.checkbox.connect("toggled", del_sys)
                row.path = 'System'
                row.set_tooltip_text(primary_label)
                insert_row(row, 0)

        # Creates List Box rows based on certificates in file index
        for k, v in self._f_index.items():
            if v.get('installed') == installed:
                if str(k.parent.name) == 'nssdb':
                    primary_label = "Chrome/Evolution"
                elif v.get('modtime') is not None:
                    primary_label = k.parents[0].name.title()
                else:
                    primary_label = k.parents[1].name.title()
                secondary_label = f"*../{k.parent.name}/{k.name}"
                secondary_label = str(k)
                row = ListBoxRow(primary_label, secondary_label)
                row.path = k
                row.set_tooltip_text(str(k))
                insert_row(row)

        self.select_certs_lb.show_all()
        self._notify.cancel()
        self._error_notify()
        self.action_box.set_sensitive(True)
        self.certs_next_btn.get_parent().foreach(toggle_sens, True)
        if cert_expire > 0:
            self.certs_next_btn.set_visible(True)
            self.certs_next_btn.set_sensitive(False)
        else:
            self.certs_next_btn.set_visible(False)
            text = "System Certificate is not installed, please install it."
            self._notify.notification(text)


    def _reset(self, settings_reset=True):
        if settings_reset:
            added_dirs = self.settings.get_strv('added-dirs')
            added_dirs = [Path(d) for d in added_dirs]
            installed = [p for p,v in self._f_index.items()
                                    if v.get('installed')]
            dirs_kept = set()
            for path in added_dirs:
                for path in installed:
                    try: # Keeps only installed files paths
                        if path.relative_to(dir_):
                            dirs_kept.add(str(path.parent))
                    except ValueError as e:
                        pass
            self.settings.reset('added-dirs')
            self.settings.reset('banned-dirs')
            if dirs_kept:
                self.settings.set_strv('added-dirs', list(dirs_kept))
        file_index_path = self.data_dir / "cert_index.pkl"
        if file_index_path.exists():
            file_index_path.unlink()
        self._f_index = {}
        self._indexer_ran = False
        self._delete_lb_children()

    ## Functions ran seperatly in an asynchronous thread using the Gio.Task API.
    @gasync_task(method=True)
    def _reset_gasync(self):
        self._reset()

    @gasync_task(method=True)
    def _check_all_cert_status(self):
        self._check_sys_cert_status(hard_check=True)
        for db,v in self._f_index.items():
            file_key = v['db_name']
            if v.get('modtime'):
                self._check_pem_status(db, file_key)
            else:
                self._check_cert_status(db, file_key)
            cert_db = {}
            cert_bundles = {}
            cert_db.update(cert_bundles)

    @gasync_task(method=True)
    def _inst_sys_certs_gasync(self, action):
        file_key = check_p11k()
        self._inst_sys_certs(action, file_key)

    @gasync_task(method=True)
    def _find_certs(self, path=None):
        # Ensures that once this function has run at least once,
        #that it will not be called again
        def glob_search(dir_):
            # db = database
            for db in dir_.rglob('cert9.db'):
                file_key = db.name
                if db.parent.name == 'nssdb':
                    file_key = f'{db.parent.name}/{db.name}'
                self._check_cert_status(db, file_key)

            #cb_sufx = ['.pem', '.crt']
            #search = [cb for cb in dir_.rglob('*cert*.[c-p][e-r][m-t]')
            #           if cb.suffix in cb_sufx and

            # ca = cert bundle
            search = [cb for cb in dir_.rglob('*cert*.pem')
                        if 'mitm' not in cb.name.lower() and
                        'private' not in cb.name.lower() and
                        'test' not in str(cb).lower()]
            search.sort(key=lambda cb: (-len(str(cb)), str(cb)), reverse=True)
            for cb in search:
                file_key = cb.suffix
                self._check_pem_status(cb, file_key)

        def index(list_):
            for d in list_:
                glob_search(d)
            self._dump_pickle()

        dir_list = []
        home = Path.home()

        # Validates all cert files still exists.
        if self._f_index and not self._indexer_ran:
            self._f_index = {p:v for p,v in self._f_index.items() if p.exists()}
            cert_db = {}
            cert_bundles = {}
            for p,v in self._f_index.items():
                if p.exists() and v.get('modtime'):
                    cert_bundles[p] = v
                    mod_time = v.get('modtime')
                    if mod_time > 0 and mod_time != p.stat().st_mtime:
                        f_key = v['db_name']
                        cmd = self._cert_cmd_factory(f_key, Action.INSTALL, p)
                        self._run.exe(cmd, get_output=True, flag=flags)
                        self._check_pem_status(p, f_key)
                elif p.exists:
                    cert_db[p] = v
            cert_db.update(cert_bundles)
            self._f_index = cert_db
            self._check_sys_cert_status()
        elif not self._indexer_ran:
            self._check_sys_cert_status(hard_check=True)

        if not self._indexer_ran:
            self._indexer_ran = True

        if path:
            dir_list.append(path)
            index(dir_list)
        elif not self._f_index:
            path = home
            xdg_user_dirs = self.settings.get_strv('xdg-user-dirs')
            usr_ban_dirs = self.settings.get_strv('banned-dirs')
            try: #In case dirs don't use XDG dirs spec
                ban_dirs = [Path(GLib.get_user_special_dir(
                    getattr(GLib.UserDirectory, d))) for d in xdg_user_dirs]
            except Exception as e:
                ban_dirs = []
            #https://specifications.freedesktop.org/trash-spec/trashspec-latest.html
            ban_dirs.append(self.data_dir.parent / 'Trash')
            ban_dirs.append(Path(GLib.get_user_cache_dir()))
            ban_dirs.extend([Path(d) for d in usr_ban_dirs])
            dir_list = [d for d in path.iterdir()
                            if d.is_dir() and d not in ban_dirs]
            added_dirs = self.settings.get_strv('added-dirs')
            if added_dirs:
                dir_list.extend([Path(d) for d in added_dirs if exists(d)])
            dir_list.sort(key=lambda d: d.name.startswith('.'), reverse=True)
            index(dir_list)

    @gasync_task(method=True)
    def _user_banned_dir(self, dir_: Path):
        # Initialize and set mandatory and non-mandatory vars
        home = Path.home()
        added_dirs = set(self.settings.get_strv('added-dirs'))
        ban_dirs = set(self.settings.get_strv('banned-dirs'))
        installed = []
        not_installed = []
        index_editted = False
        dirs_kept = set()

        for p,v in self._f_index.items():
            if v.get('installed'):
                installed.append(p)
            else:
                not_installed.append(p)
        if dir_ == home or dir_ == home.parent or dir_ == Path('/'):
            self._notify.notification("Invalid directory")
        elif check_path_invalid(dir_):
            self._notify.notification("Invalid directory")
        else:
            ban_dirs.add(str(dir_))
            # If ban dir is in added_dirs, keep installed dirs within it
            if str(dir_) in added_dirs:
                for file in installed:
                    try: # Keeps only installed files dirs
                        if file.relative_to(dir_):
                            dirs_kept.add(str(file.parent))
                    except ValueError as e:
                        pass
                added_dirs.remove(str(dir_))
                added_dirs = added_dirs.union(dirs_kept)
                self.settings.set_strv('added-dirs', list(added_dirs))
            # Remove any non-installed dirs within banned dirs from index
            for file in not_installed:
                try:
                    if file.relative_to(dir_):
                        self._f_index.pop(file)
                        if not index_editted:
                            index_editted = True
                except ValueError as e:
                    pass
            # Save index if editted
            if index_editted:
                self._dump_pickle()
            # Finally set new banned-dirs
            self.settings.set_strv('banned-dirs', list(ban_dirs))

    @gasync_task(method=True)
    def _exec_cert_cmds(self, action):
        if action == Action.REMOV:
            if 'System' in self._selected_certs:
                file_key, _ = self.settings.get_value('system-cert')
                self._inst_sys_certs(action, file_key)


        for cert in self._selected_certs:
            if cert == 'System':
                continue
            file_key = self._f_index[cert].get('db_name')
            if cert.suffix == '.pem':
                cmd = self._cert_cmd_factory(file_key, action, cert)
            else:
                cmd = self._cert_cmd_factory(file_key, action, cert.parent)

            if os.access(str(cert), os.W_OK):
                self._run.exe(cmd)
            else:
                self._run.exe(cmd, root=True)

            if cert.suffix == '.pem':
                self._check_pem_status(cert, file_key)
            else:
                self._check_cert_status(cert, file_key)
        self._dump_pickle()


    ## UI Callback functions
    # Gtk Template Callbacks
    def selected_cb(self, *args):
        selected_paths = [c.path for c in self.select_certs_lb.get_children()
                                    if c.checkbox.get_active()]
        if selected_paths:
            self.certs_next_btn.set_sensitive(True)
        else:
            self.certs_next_btn.set_sensitive(False)
        self._selected_certs = selected_paths

    # Callbacks connected on init
    def select_all_cb(self, checkbox):
        check_box_state = checkbox.get_active()
        for child in self.select_certs_lb.get_children():
            if child.checkbox.get_active() != check_box_state:
                child.checkbox.set_active(check_box_state)
        self.selected_cb()

    @Gtk.Template.Callback()
    # Makes sure everything gets to the right destination.
    def route_cb(self, lb, lb_row=None, data=None):
        def finish_process(res, Label):
            header = self.menu.get_parent().foreach(toggle_sens, True)
            # Replace with process output call
            text = 'Done'
            Label.set_markup(
                f'<span weight="ultrabold" font="Sans Regular 16">{text}</span>'
                )
            res_status = 'done'
            self._process.cancel(res_status)
            self.emit('certs_installed', True)

        if lb_row:
            obj = lb_row
        else:
            obj = lb
        map_entry = self.stack_map[obj]

        if map_entry['action'] == Action.INSTALL_SYS:
            par_func = partial(self._inst_sys_certs_gasync,
                                    action=map_entry['action'])
            if data:
                par_func_cb = data
            else:
                self.menu.get_parent().foreach(toggle_sens, False)
                lab = self._process.spinner('Installing Certificate to System',
                                             True)
                par_func_cb = partial(finish_process, Label=lab)
            run_gasync_task(par_func, par_func_cb)

        elif map_entry['action'] == Action.INSTALL:
            self._notify.spinner("Loading")
            if not self.action_box.get_visible():
                self.action_box.set_visible(True)
            self.action_box.set_sensitive(False)
            self.select_all_chck.set_active(False)
            self.header_stack.get_child_by_name(map_entry['head']).set_subtitle(
                "Install Certificates"
            )
            self.header_stack.get_child_by_name(map_entry['head']).foreach(
                toggle_sens, False
            )
            self.select_certs_lab.set_text(
                "Install NoSurfin's certificate to app certificate stores."
            )
            if self._indexer_ran and not data:
                self._update_listbox(installed=False)
            elif data:
                par_func = partial(self._find_certs, path=data)
                run_gasync_task(par_func, self._update_listbox)
            else:
                run_gasync_task(self._find_certs, self._update_listbox)
            self._prev_action = map_entry['action']

        elif map_entry['action'] == Action.REMOV:
            self._notify.spinner("Loading")
            self.select_all_chck.set_active(False)
            self.action_box.set_visible(False)
            self.header_stack.get_child_by_name(map_entry['head']).set_subtitle(
                "Remove Certificates"
            )
            self.header_stack.get_child_by_name(map_entry['head']).foreach(
                toggle_sens, False
            )
            self.select_certs_lab.set_text(
                "Remove NoSurfin's certificate from system"
                " and app certificate stores."
            )
            if self._indexer_ran:
                self._update_listbox(installed=True)
            else:
                par_func_cb = partial(self._update_listbox, installed=True)
                run_gasync_task(self._find_certs, par_func_cb)
            self._prev_action = map_entry['action']

        elif map_entry['action'] == Action.CHECK:
            par_func = partial(self._exec_cert_cmds, action=self._prev_action)
            if data:
                par_func_cb = data
            else:
                self.menu.get_parent().foreach(toggle_sens, False)
                lab = self._process.spinner(
                    f"{self._prev_action.name.title()}ing certificates...",True)
                par_func_cb = partial(finish_process, Label=lab)
            run_gasync_task(par_func, par_func_cb)
            self._prev_action = map_entry['action']

        self.main_stack.set_visible_child_full(map_entry['main'],
                                               map_entry['trans'])
        self.header_stack.set_visible_child_full(map_entry['head'],
                                                 map_entry['trans'])

    @Gtk.Template.Callback()
    def add_dir_cb(self, *args):
        def user_added_dir_cb(dir_: Path):
            home = Path.home()
            ban_dirs = set(self.settings.get_strv('banned-dirs'))
            added_dirs = set(self.settings.get_strv('added-dirs'))
            if dir_ == home or dir_ == home.parent or dir_ == Path('/'):
                self._notify.notification("Invalid path")
            elif check_path_invalid(dir_):
                self._notify.notification("Invalid path")
            elif not os.access(str(dir_), os.R_OK):
                self._notify.notification("Invalid path")
            else:
                added_dirs.add(str(dir_))
                if str(dir_) in ban_dirs:
                    ban_dirs.remove(str(dir_))
                    self.settings.set_strv('banned-dirs', list(ban_dirs))
                self.settings.set_strv('added-dirs', list(added_dirs))
                self.route_cb(lb=self.certs_install, data=dir_)

        open_dir('Choose a Directory to Add', user_added_dir_cb)

    @Gtk.Template.Callback()
    def ban_dir_cb(self, *args):
        def ban_dir_gasync_cb(directory: Path):
            self._notify.spinner("Working...")
            def finish_cb(obj):
                self.route_cb(lb=self.certs_install)
            par_func_cb = partial(self._user_banned_dir, dir_=directory)
            run_gasync_task(par_func_cb, finish_cb)
        open_dir('Choose a Directory to Ban', ban_dir_gasync_cb)

    @Gtk.Template.Callback()
    def export_cert_cb(self, button):
        def export_cb(dir_: Path):
            if self.cert_path.exists():
                copy2(str(self.cert_path), str(dir_))
                self._notify.notification(f"Successfully exported to {dir_}")
            else:
                self._error_buffer = ("Cannot find certificate. Please remove"
                " and install the system certificate, then try again.")
                self._error_notify()
        open_dir(f'Choose a Directory to Export {self.cert_path.name}',
                                                            export_cb)

    @Gtk.Template.Callback()
    def check_cert_status_all_cb(self, button):
        self._notify.spinner("Working")
        def finish_notify(*args):
            self._notify.notification("Successfully checked all cert statuses.")
        run_gasync_task(self._check_all_cert_status, finish_notify)

    @Gtk.Template.Callback()
    def reset_index_cb(self, button):
        def reindex_confirm_cb(*args):
            self._notify.spinner("Working...")
            self._reset(settings_reset=False)
            self._notify.notification("Successfully reset index.")
        message = ("This action deletes the currently stored certificate index."
        " Loading certificates for the first time again will take some time"
        " after this. Do you wish to continue?")
        message_dialog(self, message, reindex_confirm_cb, yes_no=True)

    @Gtk.Template.Callback()
    def reset_wiz_cb(self, button):
        def reset_wiz_confirm_cb(*args):
            toggle_sens_btns_recur(self.header_stack, False)
            self.certs_remove.get_parent().set_sensitive(False)
            self._notify.spinner("Working...")
            def finishing_cb(*args):
                toggle_sens_btns_recur(self.header_stack, True)
                self.certs_remove.get_parent().set_sensitive(True)
                self._notify.notification("Successfully reset wizard.")
            if not self._f_index:
                run_gasync_task(self._find_certs, reset_wiz_confirm_cb)
            else:
                run_gasync_task(self._reset_gasync, finishing_cb)
        message = ("This action will reset all added and banned directories as "
        "well as the certificate index. Do you wish to continue?")
        message_dialog(self, message, reset_wiz_confirm_cb, yes_no=True)

    @Gtk.Template.Callback()
    def close_cb(self, *args):
        self.destroy()
