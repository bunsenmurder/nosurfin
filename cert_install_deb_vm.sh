#!/bin/sh
if [ "$(id -u)" != "0" ]
then
  echo "Please run this script as root\n"
  exit 1
fi
openssl x509 -in ./mitmproxy-ca-cert.pem -inform PEM -out mitmproxy-ca-cert.crt
cp ./mitmproxy-ca-cert.crt /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt
update-ca-certificates

