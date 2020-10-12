# dbus_tools.py
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

import os
from gi.repository import GLib, Gio, GObject

def ProxyFactorySync(name, path, iface):
    print(f"Finalizing D-Bus proxy connection to {path}")
    try:
        proxy = Gio.DBusProxy.new_for_bus_sync(
            bus_type=Gio.BusType.SESSION,
            flags=Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES,
            info=None, name=name, object_path=path,
            interface_name=iface
        )
        print(f"Success: D-Bus proxy object obtained {iface}")
    except GLib.Error as e:
        print(f"Error: Could not connect to logind: {e.message}")
        return
    return proxy

class ProxyFactory(GObject.GObject):
    __gsignals__ = {'proxy_done':(GObject.SignalFlags.RUN_LAST, GObject.TYPE_OBJECT, (GObject.TYPE_OBJECT,))}
    def __init__(self, name, path, iface):
        super().__init__()
        self.name = name

    def create_proxy(self):
        print("Initializing D-Bus proxy object for logind")
        # Initialize creation of Dbus Proxy
        Gio.DBusProxy.new_for_bus(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES,
            None,
            self.name,
            path,
            iface,
            None,
            self.return_proxy,
            path, iface
        )
    def return_proxy(self, proxy, res, path, iface):
        print(f"Finalizing D-Bus proxy connection to {path}")
        try:
            proxy = proxy.new_finish(res)
            print(f"Success: D-Bus proxy object obtained for interface{iface}")
            self.emit('proxy_done', proxy)
        except GLib.Error as e:
            print(f"Error: Could not connect to logind: {e.message}")
            self.proxy_failed = True
            return

    def destroy(self):
        self.destroy()



class CatchSleep(GObject.GObject):
    def __init__(self, app, window):
        super().__init__()
        self._app = app
        self._window = window
        self._logind_proxy = None
        self._receiver = None
        self._create_proxy()
        self._app.connect("notify::clock-active", self._on_clock_active)

    def _create_proxy(self):
        print("Initializing D-Bus proxy object for logind")
        # Initialize creation of Dbus Proxy
        Gio.DBusProxy.new_for_bus(
            bus_type=Gio.BusType.SYSTEM,
            flags=Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES,
            info=None,
            name='org.freedesktop.login1',
            object_path='/org/freedesktop/login1',
            interface_name='org.freedesktop.login1.Manager',
            cancellable=None,
            callback=self._return_proxy
        )

    def _return_proxy(self, proxy, res):
        print("Finalizing D-Bus proxy connection to logind")
        try:
            self._logind_proxy = proxy.new_finish(res)
            print("Success: D-Bus proxy object obtained")
            if self._app.props.clock_active:
                self._create_signal_receiver()
        except GLib.Error as e:
            print(f"Error: Could not connect to logind: {e.message}")
            return

    def _on_clock_active(self, *args):
        if self._app.props.clock_active:
            print("Clock started")
            self._create_signal_receiver()

        if not self._app.props.clock_active:
            print("Clock closed")
            self._close_signal_reciever()

    def _create_signal_receiver(self):
        print("Setting up logind signal receiver")
        try:
            self._receiver = self._logind_proxy.connect(
                "g-signal", self._reset_clock)
            print("Success: Signal receiver is up")
        except GLib.Error as e:
            print(f"Error: Could not setup receiver: {e}")


    def _close_signal_reciever(self, *args, **kwargs):
        print("Closing reciever connection")
        try:
            self._logind_proxy.disconnect(self._receiver)
        except Exception as e:
            if TypeError:
                return
            else:
                print(f"Error: Session already disconnected: {e}")


    def _reset_clock(self, proxy, sender, signal, parameters):
        if signal != "PrepareForSleep":
            return

        (not_woke, ) = parameters
        # Resets the clock, once awoken from sleep
        if not_woke is False:
            print("BIG WOKE")
            self._window.check_for_block()


class UrlMgrProxy(GObject.GObject):
    def __init__(self):
        super().__init__()
        self._logind_proxy = None
        self._receiver = None
        self.name = 'com.github.bunsenmurder.NSUrlManager'
        self.obj_path = '/com/github/bunsenmurder/NSUrlManager'
        self.m_iface = 'com.github.bunsenmurder.NSUrlManager'

    def create_proxy(self):
        # Initialize creation of Dbus Proxy
        if self._logind_proxy is None:
            print("Initializing D-Bus proxy object for Url Manager")
            Gio.DBusProxy.new_for_bus(
                bus_type=Gio.BusType.SYSTEM,
                flags=Gio.DBusProxyFlags.DO_NOT_CONNECT_SIGNALS,
                info=None,
                name=self.name,
                object_path=self.obj_path,
                interface_name='org.freedesktop.DBus.Properties',
                cancellable=None,
                callback=self._return_proxy
            )

    def _return_proxy(self, proxy, res):
        print("Finalizing D-Bus proxy connection to UrlMgr")
        try:
            self._logind_proxy = proxy.new_finish(res)
            print("Success: D-Bus proxy object obtained")
        except GLib.Error as e:
            print(f"Error: Could not connect to urlmgr: {e.message}")
            return

    def set_host_token(self, value, notify_obj):
        host_token = self._get_host_token()
        if host_token:
            text = "Couldn't add to block, out of Host Tokens!"
            notify_obj.notification(text)
            # Place notification telling user they are out of host tokens,
            #and any more added ignore hosts will be applied on next block run.
        else:
            host_url = GLib.Variant.new_string(value)
            self._logind_proxy.Set('(ssv)', self.m_iface, 'Token', host_url)

    def _get_host_token(self):
        host_token = self._logind_proxy.Get('(ss)',self.m_iface, 'Token')
        return host_token

    def set_block_url(self, value):
        block_url = GLib.Variant.new_string(value)
        self._logind_proxy.Set('(ssv)', self.m_iface, 'Url', block_url)

        
