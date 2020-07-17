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
from os import path
from subprocess import run
# TODO: Make optional arguments that override these if specified
# Diretory script is being run from
current_dir = path.dirname(path.realpath(__file__))
# Default args used to generate systemd configs, that can be overridden.
mitm_path = '/usr/bin/mitmdump'
filter_path = path.join(current_dir, 'filters/blocklist.py')
mitm_user = 'root'

# Generates mitm proxy command to start the block
mitm_cmd = f'{mitm_path} -s {filter_path} --mode transparent ' \
           f'--ignore-hosts google.com:443 ' \
           f'--set block_global=false --set flow_detail=0 ' \
           f'--set console_eventlog_verbosity=error ' \
           f'--set termlog_verbosity=error'

# Shell scripts run by systemd
net_setup = path.join(current_dir, 'sh_scripts/network_setup.sh')
net_reset = path.join(current_dir, 'sh_scripts/network_reset.sh')
check_block = path.join(current_dir, 'sh_scripts/check_block.sh')

# Cleans up timer stamp and starts systemd jobs
systemd_cmds = ['rm -f /var/lib/systemd/timers/stamp-stop_ns_block.timer',
                'systemctl daemon-reload',
                'systemctl enable --now ns_block',
                'systemctl enable --now stop_ns_block.timer']

def _time_calc(time: int):
    end_time = datetime.now() + timedelta(minutes=int(time))
    end_time = end_time - timedelta(microseconds=end_time.microsecond)
    print(f"Timer will complete at {end_time.strftime('%I:%M %p')}")
    print(f"Time left {end_time - datetime.now()}")
    return end_time


def _save_file(filename, file):
    dirname = '/etc/systemd/system'
    filepath = path.join(dirname, filename)
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
                                  'Description=Shuts down ns_block',
                                  'Conflicts=ns_block.service',
                                  '[Service]',
                                  'Type=oneshot',
                                  f'ExecStart={net_reset}',
                                  f'ExecStartPost={check_block}',
                                  'StandardOutput=journal',
                                  ],
        'ns_block.service': ['[Unit]',
                             'Description=Run mitm with filter',
                             'RefuseManualStop=true',
                             '[Service]',
                             'Type=simple',
                             f'User={mitm_user}',
                             f'ExecStartPre={net_setup}',
                             f'ExecStart={mitm_cmd}',
                             'ExecStop=/bin/kill -2 $MAINPID',
                             '[Install]',
                             'WantedBy=multi-user.target']}

    for k, v in file_dict.items():
        print("Breakpoint")
        _save_file(k, v)

    for cmd in systemd_cmds:
        run(cmd, shell=True)


time = sys.argv[1]
set_block(time)
