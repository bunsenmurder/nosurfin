#!/bin/bash
ns_block='ns_block'
stop_ns_block='stop_ns_block.timer'
stop_ns_block_path='/etc/systemd/system/stop_ns_block.timer'
block_time=$(cat $stop_ns_block_path | grep OnCalendar | awk 'match($0, "[0-9]+-[0-9]+-[0-9]+[[:space:]][0-Z]+") {print substr($0, RSTART, RLENGTH)}')

if [[ $(date +"%Y-%m-%d %H:%M:%S") < $(date --date="$block_time" +"%Y-%m-%d %H:%M:%S") ]]
then 
    echo "This time is wack, restarting block."
    systemctl start "$ns_block"
else
    echo "Good job kid, you made it."
    systemctl disable "$ns_block"
    systemctl disable "$stop_ns_block"
    systemctl stop "$stop_ns_block"
fi
echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
