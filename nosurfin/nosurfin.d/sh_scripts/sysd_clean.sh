#!/bin/sh
# Clean up script to uninstall 
#Searchs for and reloads changed object
systemctl daemon-reload
# Cleans up any deleted systemd config files
systemctl reset-failed
#Removes rougue time stamps
rm -f /var/lib/systemd/timers/"$1"
