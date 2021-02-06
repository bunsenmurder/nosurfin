# blocklist.py
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
import asyncio

# Check if jeepney is installed, if not disables jeepney
jeepney = False
try:
    from jeepney.integrate.asyncio import connect_and_authenticate, Proxy
    from jeepney.bus_messages import message_bus, MatchRule
    from jeepney import DBusAddress, new_method_call
    jeepney = True
except ImportError as e:
    print(e)
    pass
if jeepney:
    urlmgr = DBusAddress('/com/github/bunsenmurder/NSUrlManager',
                        bus_name='com.github.bunsenmurder.NSUrlManager',
                        interface='org.freedesktop.DBus.Properties')
    get_token = new_method_call(urlmgr, 'Get', 'ss',
                                (urlmgr.bus_name, 'Token'))
blocklist = []
#Find HTML Path
html_path = path.join(path.dirname(path.realpath(__file__)), 'index.html')
#Load block html page
with open(html_path, "r", encoding='utf-8') as f:
    html_page = f.read()
block_response = http.HTTPResponse.make(
    200, html_page, {"Content-Type": "text/html"})

async def signal_listen(loader, ignore_list):
    _, protocol = await connect_and_authenticate(bus="SYSTEM")
    session_proxy = Proxy(message_bus, protocol)

    # Create a "signal-selection" match rule
    match_rule = MatchRule(
        type="signal",
        sender=urlmgr.bus_name,
        interface=urlmgr.interface,
        member="PropertiesChanged",
        path=urlmgr.object_path,
    )

    HostAddedStatus = False
    resp = await protocol.send_message(get_token)
    PrevToken = resp[0][1]
    if PrevToken:
        ignore_list.append(f'{PrevToken.rstrip()}:443')
        loader.master.server.config.check_filter = \
            HostMatcher("ignore", ignore_list)
        HostAddedStatus = True

    # Callback
    def on_properties_changed(message):
        prop, type_value = message[1][0]
        _, value = type_value
        if prop == 'Token':
            nonlocal HostAddedStatus
            if not HostAddedStatus:
                HostAddedStatus = True
                nonlocal loader
                nonlocal ignore_list
                ignore_list.append(f'{value.rstrip().lower()}:443')
                loader.master.server.config.check_filter = \
                    HostMatcher("ignore", ignore_list)
        elif prop == 'Url':
            global blocklist
            blocklist.append(value)

    # Attach call back to signal
    protocol.router.subscribe_signal(
        callback=on_properties_changed,
        path=urlmgr.object_path,
        interface=urlmgr.interface,
        member="PropertiesChanged"
    )

    # Add match rule to be notified of signal
    await session_proxy.AddMatch(match_rule)

def load(loader):
    # Within this stage both the initialized server objects
    # and custom options can be accessed early.
    # The server object provides the check_filter attribute which holds
    # a Host Matcher object, which can be replaced with our own
    # HostMatcher object to avoid adding too many command line options.
    ignorelist = []
    if 'blocklist' in loader.master.options.deferred:
        blocklist_path = loader.master.options.deferred.pop('blocklist')
        if isinstance(blocklist_path, str) and True:
            with open(blocklist_path, "r") as f:
                for line in f:
                    blocklist.append(line.rstrip().lower())
    if 'ignorehostlist' in loader.master.options.deferred:
        # TODO: Look into domain/ip validation for ignore list
        # TODO: Add regex patterns for more efficient pattern matching
        ignorelist_path = loader.master.options.deferred.pop('ignorehostlist')
        if isinstance(ignorelist_path, str) and True:
            with open(ignorelist_path, "r") as f:
                ignorelist = [f'{line.rstrip()}:443' for line in f]
                # Patch HostMatcher object with all ignored hosts
                loader.master.server.config.check_filter = \
                    HostMatcher("ignore", ignorelist)
    # Checks if jeepney is installed
    if jeepney:
        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(
            signal_listen(loader, ignorelist), loop)


# This decorator allows concurrent blocking request interception
@concurrent
def request(flow):
    pretty_url = flow.request.pretty_url.lower()
    if any(url in pretty_url for url in blocklist):
        flow.response = block_response
