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

from gi.repository import Gtk, GLib, GObject, Gdk

css = b'.clock {font-size: 60px;} ' \
      b'.colon {font-size: 60px; color: @fg_color;} ' \
      b'spinbutton:disabled{color: @fg_color;} ' \
      b'spinbutton > entry:disabled {border-radius: 10; border-style: none;}' \
      b'spinbutton > button:disabled {background-color: transparent; ' \
      b'color:transparent; border-color: transparent;} '
def _time_form(t):
    h, remainder = divmod(t, 3600)
    m, s = divmod(remainder, 60)
    return h, m, s

@Gtk.Template(resource_path='/com/github/bunsenmurder/NoSurfin/Clock.ui')
class Timer(Gtk.Grid):
    # Set GObject things and retrieve so template objects
    __gtype_name__ = "Timer"
    __gsignals__ = {'timer_done':(GObject.SignalFlags.RUN_LAST, None, ())}

    h = Gtk.Template.Child()
    m = Gtk.Template.Child()
    s = Gtk.Template.Child()

    def __init__(self, time):
        super().__init__()
        self.style = Gtk.CssProvider()
        self.style.load_from_data(css)
        self.screen = Gdk.Screen.get_default()
        self.ctx = Gtk.StyleContext.add_provider_for_screen(
            self.screen, self.style, 400)
        self.count_down(time)

    def count_down(self, time):
        if time > 0:
            h, m, s = _time_form(time)
            self.s.set_text(f'{s:02d}')
            self.m.set_text(f'{m:02d}')
            self.h.set_text(f'{h:02d}')
            GLib.timeout_add_seconds(1, self.count_down, time - 1)
        else:
            self.s.set_text(f'{0:02d}')
            self.m.set_text(f'{0:02d}')
            self.h.set_text(f'{0:02d}')
            self.emit('timer_done')

        return False
