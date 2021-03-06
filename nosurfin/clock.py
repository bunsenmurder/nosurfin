# clock.py
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

from gi.repository import Gtk, GLib, GObject

def time_format(t):
    h, remainder = divmod(t, 3600)
    m, s = divmod(remainder, 60)
    return h, m, s

@Gtk.Template(resource_path='/com/github/bunsenmurder/NoSurfin/ui/Clock.ui')
class Timer(Gtk.Box):
    # Set GObject things and retrieve so template objects
    __gtype_name__ = "Timer"
    __gsignals__ = {'timer_done':(GObject.SignalFlags.RUN_LAST, None, ())}

    h = Gtk.Template.Child()
    m = Gtk.Template.Child()
    s = Gtk.Template.Child()
    frame = Gtk.Template.Child()

    def __init__(self, time):
        super().__init__()
        self.count_down(time)

    def count_down(self, time):
        if time > 0:
            h, m, s = time_format(time)
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
