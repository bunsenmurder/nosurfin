#!/bin/sh
if [ "$(id -u)" != "0" ]
then
  echo "Please run this script as root\n"
  exit 1
fi
mitmproxy &
#last_pid=$!
sleep 3
#kill $last_pid
# Only if the distro does not support the certificate format
#openssl x509 -in ~/.mitmproxy/mitmproxy-ca-cert.pem -inform PEM -out ~/.mitmproxy/mitmproxy-ca-cert.crt
trust anchor --store ~/.mitmproxy/mitmproxy-ca-cert.pem
# The line below is our workaround for mozilla based applications that are not using pll-kit.
# -d would be the location of firefox profile, -i would be location of the cert file, -n would be the name. 
# certutil -d /Home/YOURUSERNAME/mozilla/firefox/INSERTFIREFOX.PROFILE -A -i ~/.mitmproxy/mitmproxy-ca-cert.pem -n "mitmproxy ca" -t C,,
# Ex: 
# certutil -d firefox/*.default-esr -A -i ~/.mitmproxy/mitmproxy-ca-cert.pem -n "mitmproxy ca" -t C,,
