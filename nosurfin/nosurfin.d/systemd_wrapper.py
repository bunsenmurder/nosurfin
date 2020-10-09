# systemd_wrapper.py
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

import sys
from datetime import datetime, timedelta
from os.path import join, dirname, realpath, abspath, exists
from subprocess import run
#Get command line arguments
time = sys.argv[1]
blocklist_file = str(join(sys.argv[2], 'blocklist.txt'))
ignorelist_file = str(join(sys.argv[2], 'ignorelist.txt'))
# Default args used to generate systemd configs, that can be overridden.
mitm_path = str(sys.argv[3])
current_dir = dirname(realpath(__file__))
filter_path = join(current_dir, 'filters/blocklist.py')

# Finds the dbus service binary
dbus_ser = 'nosurfin/nsurlmanager'
usr_dir = abspath(join(current_dir,'../../../..'))
m_arch = sys.implementation._multiarch
urlmgr_path = join(usr_dir, 'lib', dbus_ser)
# Compatiablilty for diffrent linux systems
if not exists(urlmgr_path):
    urlmgr_path = abspath(join(usr_dir, '../lib', dbus_ser))
    if not exists(urlmgr_path):
        urlmgr_path = abspath(join(usr_dir, 'lib', m_arch, dbus_ser))
        if not exists(urlmgr_path):
            urlmgr_path = abspath(join(usr_dir, '../lib', m_arch, dbus_ser))


# Generate mitm proxy command to start the block
mitm_cmd = f'{mitm_path} -s {filter_path} --mode transparent ' \
           f'--set block_global=false --set flow_detail=0 ' \
           f'--set console_eventlog_verbosity=error ' \
           f'--set termlog_verbosity=error '

if exists(blocklist_file):
    mitm_cmd = mitm_cmd + f'--set blocklist={blocklist_file} '
if exists(ignorelist_file):
    mitm_cmd = mitm_cmd + f'--set ignorehostlist={ignorelist_file} '
# Shell scripts run by systemd
net_setup = join(current_dir, 'sh_scripts/network_setup.sh')
net_reset = join(current_dir, 'sh_scripts/network_reset.sh')
check_block = join(current_dir, 'sh_scripts/check_block.sh')

# Cleans up timer stamp and starts systemd jobs
systemd_cmds = ['rm -f /var/lib/systemd/timers/stamp-stop_ns_block.timer',
                'systemctl daemon-reload',
                'systemctl enable --now ns_block',
                'systemctl enable --now stop_ns_block.timer']

def _time_calc(time: int):
    end_time = datetime.now() + timedelta(minutes=int(time))
    end_time = end_time - timedelta(microseconds=end_time.microsecond)
    #print(f"Timer will complete at {end_time.strftime('%I:%M %p')}")
    #print(f"Time left {end_time - datetime.now()}")
    return end_time


def _save_file(filename, file):
    dirname = '/etc/systemd/system'
    filepath = join(dirname, filename)
    with open(filepath, "w+") as f:
        for line in file:
            f.write(line)
            f.write("\n")


def set_block(time):
    end_time = _time_calc(time)
    file_dict = {
        'stop_ns_block.timer': ['[Unit]',
                                'Description=Timer to activate '
                                'stop ns_block.service',
                                '[Timer]',
                                'Unit=stop_ns_block.service',
                                f'OnCalendar= {end_time.isoformat(sep=" ")}',
                                'Persistent=true',
                                '[Install]',
                                'WantedBy=basic.target'],
        'stop_ns_block.service': ['[Unit]',
                                  'Description=Shutdown of ns_block.service',
                                  'Conflicts=ns_block.service',
                                  'Conflicts=dbus-com.github.bunsenmurder.NSUrlManager.service',
                                  '[Service]',
                                  'Type=oneshot',
                                  f'ExecStart={net_reset}',
                                  f'ExecStartPost={check_block}',
                                  'StandardOutput=journal',
                                  ],
        'ns_block.service': ['[Unit]',
                             'Description=Run mitm with filter',
                             'RefuseManualStop=true',
                             'Requires=dbus-com.github.bunsenmurder.NSUrlManager.service',
                             '[Service]',
                             'Type=simple',
                             f'ExecStartPre={net_setup}',
                             f'ExecStart={mitm_cmd}',
                             'ExecStop=/bin/kill -2 $MAINPID',
                             '[Install]',
                             'WantedBy=multi-user.target'],
        'dbus-com.github.bunsenmurder.NSUrlManager.service':
                            ['[Unit]',
                             'Description=DBus service accessed by mitmproxy.',
                             '[Service]',
                             'Type=dbus',
                             'BusName=com.github.bunsenmurder.NSUrlManager',
                             f'ExecStart={urlmgr_path}',
                             '[Install]',
                             'WantedBy=multi-user.target']
                             }

    for k, v in file_dict.items():
        _save_file(k, v)

    for cmd in systemd_cmds:
        run(cmd, shell=True)

set_block(time)
