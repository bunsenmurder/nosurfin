# window.py
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


class CatchSleep(GObject.GObject):
    def __init__(self, window):
        super().__init__()
        self._window = window
        self._logind_proxy = None
        self._receiver = None
        self._create_proxy()
        self._window.connect("notify::clock-active", self._on_clock_active)

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
        print(f"Finalizing D-Bus proxy connection to logind")
        try:
            self._logind_proxy = proxy.new_finish(res)
            print(f"Success: D-Bus proxy object obtained")
            if self._window.props.clock_active:
                self._create_signal_receiver()
        except GLib.Error as e:
            print(f"Error: Could not connect to logind: {e.message}")
            return

    def _on_clock_active(self, *args):
        if self._window.props.clock_active:
            print("Clock started")
            self._create_signal_receiver()

        if not self._window.props.clock_active:
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

        if not_woke is False:
            print("BIG WOKE")
            self._window.check_for_block()
