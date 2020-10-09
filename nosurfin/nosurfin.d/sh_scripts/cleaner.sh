#!/bin/bash
# Clean up script to uninstall any type of files created by NoSurfin
if [ "$(id -u)" != "0" ]
  then
    echo "You cannot perform this action unless you are root." >&2
    exit 1
fi

if [ "$#" -lt 1 ]; then
  echo "You must supply the user home directory!"
  exit 1
fi

# Removal of ~/.local/share/nosurfin, must pass the local/share directory path
rm -rf "$1"

# Removeal of home directory, must pass the user home directory for deletion
rm -rf "$2/__pycache__"
rm -rf "$2/nosurfin.d/filters/__pycache__"

# Removes folder created by mitmproxy in root directory
rm -rf /root/.mitmproxy

#Removes all systemd related files
rm -f /etc/systemd/system/dbus-com.github.bunsenmurder.NSUrlManager.service
rm -f /etc/systemd/system/ns_block.service
rm -f /etc/systemd/system/stop_ns_block.service
rm -f /etc/systemd/system/stop_ns_block.timer
rm -f /var/lib/systemd/timers/stamp-stop_ns_block.timer

# Removes pipx environment if it is installed
rm -rf ns_dep


systemctl daemon-reload
systemctl reset-failed
