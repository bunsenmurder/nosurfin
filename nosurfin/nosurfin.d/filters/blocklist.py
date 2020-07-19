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

from mitmproxy.proxy.config import HostMatcher
from mitmproxy.script import concurrent
from mitmproxy import http
from os import path

addresses = []
#Find HTML Path
html_path = path.join(path.dirname(path.realpath(__file__)), 'index.html')
#Load block html page
with open(html_path, "r", encoding='utf-8') as f:
    html_page = f.read()
block_response = http.HTTPResponse.make(
    200, html_page, {"Content-Type": "text/html"})

def load(loader):
    # Within this stage both the initialized server objects
    # and custom options can be accessed early.
    # The server object provides the check_filter attribute which holds
    # a Host Matcher object, which can be replaced with our own
    # HostMatcher object to avoid adding too many command line options.

    if 'blocklist' in loader.master.options.deferred:
        blocklist_path = loader.master.options.deferred.pop('blocklist')
        if isinstance(blocklist_path, str) and True:
            with open(blocklist_path, "r") as f:
                for line in f:
                    addresses.append(line.rstrip())
    if 'ignorehostlist' in loader.master.options.deferred:
        # TODO: Look into domain/ip validation for ignore list
        # TODO: Add regex patterns for more efficient pattern matching
        ignorelist_path = loader.master.options.deferred.pop('ignorehostlist')
        if isinstance(ignorelist_path, str) and True:
            with open(ignorelist_path, "r") as f:
                ignore_addresses = [f'{line.rstrip()}:443' for line in f]
                loader.master.server.config.check_filter = \
                    HostMatcher("ignore", ignore_addresses)


# This decorator allows concurrent blocking request interception
@concurrent
def request(flow):
    match = any(address in flow.request.pretty_url for address in addresses)
    if match:
        flow.response = block_response
