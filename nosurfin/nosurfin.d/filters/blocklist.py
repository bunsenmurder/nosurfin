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

"""Filters urls with blocklist """

from mitmproxy import http
from mitmproxy.script import concurrent
from os import path
from gi.repository import GLib
#Paths
current_dir = path.dirname(path.realpath(__file__))
html_path = path.join(current_dir, 'index.html')
blocklist_path = path.join(GLib.get_user_data_dir(), 'nosurfin/blocklist.txt')
#blocklist_path = '/home/archbox/blocklist.txt'
#Load block html and blocklist
with open(html_path, "r", encoding='utf-8') as f:
    html_page = f.read()
with open(blocklist_path, "r") as f:
    addresses = [line.rstrip() for line in f]

#resp_pg = http.HTTPResponse.make(200, html_page, {"Content-Type": "text/html"})
# Code for blocking logic
@concurrent # This decorator allows concurrent blocking of packets
def request(flow):
    #adr_list = ctx.options.addresses
    adr_list = addresses
    match = any(address in flow.request.pretty_url for address in adr_list)
    if match:
        #flow.response = resp_pg
        flow.response = http.HTTPResponse.make(200, html_page, {"Content-Type": "text/html"})
