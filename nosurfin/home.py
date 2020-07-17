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

from gi.repository import Gtk, GObject

@Gtk.Template(resource_path='/com/github/bunsenmurder/NoSurfin/Home.ui')
class HomePage(Gtk.Grid):
    __gtype_name__ = "Home"
    __gsignals__ = {'start_block': (GObject.SignalFlags.RUN_FIRST, None, (int, ))}
    hr_spin = Gtk.Template.Child()
    m_spin = Gtk.Template.Child()
    start_btn = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hr_spin.set_text('{:02d}'.format(0))
        self.m_spin.set_text('{:02d}'.format(0))

    @Gtk.Template.Callback()
    def zero_format(self, widget):
        adj = widget.get_adjustment()
        widget.set_text('{:02d}'.format(int(adj.get_value())))
        return True

    @Gtk.Template.Callback()
    def update_start(self, widget):
        hours = self.hr_spin.get_value_as_int()
        minutes = self.m_spin.get_value_as_int()
        if hours + minutes != 0:
            self.start_btn.props.sensitive = True
            # Add theme to highlight button
            # gtk_style_context_add_class (context, "suggested-action")
        else:
            self.start_btn.props.sensitive = False

    @Gtk.Template.Callback()
    def start_clicked(self, widget):
        hours = self.hr_spin.get_value_as_int()
        minutes = self.m_spin.get_value_as_int()
        #print(f"Timer set for {hours} hours and {minutes} minutes!")
        time = (hours*60) + minutes
        self.emit('start_block', time)
