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
from datetime import datetime
from .clock import Timer
from .home import HomePage


@Gtk.Template(resource_path="/com/github/bunsenmurder/NoSurfin/ui/Window.ui")
class AppWindow(Gtk.ApplicationWindow):
    """AppWindow object

    Starts the application window which could contains either home page or
    contains a timer clock.
    """
    __gtype_name__ = "Window"
    __gsignals__ = {
        'save_block': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }
    # Make sure to use clock-active in notify signal instead of clock_active
    #clock_active = GObject.Property(type=bool, default=False)
    page_stack = Gtk.Template.Child()


    def __init__(self, app, *args, **kwargs):
        super().__init__(application=app, *args, **kwargs)
        """Initialize Application Window

        :param Application app: Application instance object
        """
        theme_classes = {
            0: ['clock_frame_1'],
            1: ['clock_frame_2', 'keycap']
        }
        self._style_classes = theme_classes[app.settings.get_enum('clock-face')]
        self._clock = None
        self._home_page = None
        self._block_exist = False
        self._app=app
        self.check_for_block()

    def check_for_block(self, file="/etc/systemd/system/stop_ns_block.timer"):
        """Checks for existing time block and
        routes to the appropriate screen. """
        try:
            with open(file) as f:
                for line in f:
                    if line.startswith('OnCalendar'):
                        time_done_cfg = line[12:].rstrip()
                        break
                    #time_done_cfg = f.readline()
            time = datetime.fromisoformat(time_done_cfg)
            if datetime.now() < time:
                self._block_exist = True
                end_time = time
            else:
                self._block_exist = False

        except (TypeError, IOError, ValueError) as e:
            self._block_exist = False

        if not self._block_exist:
            if self._home_page:
                self._transition_home()
            else:
                self._new_home()
        else:
            self._new_clock(end_time)

    def _destroy_clock(self):
        if self._clock:
            self.page_stack.remove(self._clock)
            self._clock.destroy()
            self._clock = None

    def _transition_home(self):
        self._app.props.clock_active = False
        self._home_page.show()
        self.page_stack.set_visible_child_name('home_pg')

    def _new_home(self):
        if self._app.props.clock_active:
            self._app.props.clock_active = False
        self._home_page = HomePage()
        self._home_page.connect("start_block", self._emit_time)
        self.page_stack.add_named(self._home_page, 'home_pg')
        self._home_page.show()
        self.page_stack.set_visible_child_name('home_pg')

    def _new_clock(self, end_time):
        self._destroy_clock()
        if not self._app.props.clock_active:
            self._app.props.clock_active = True
        remain = end_time - datetime.now()
        self._clock = Timer(remain.seconds)
        self._clock.connect("timer_done", self._clock_done)
        self.page_stack.add(self._clock)
        self._apply_clock_face()
        self._clock.show()
        self.page_stack.set_visible_child(self._clock)

    def _apply_clock_face(self):
        frame_style_context = self._clock.frame.get_style_context()
        for c in frame_style_context.list_classes():
            if c != 'horizontal':
                frame_style_context.remove_class(c)
        for c in self._style_classes:
            frame_style_context.add_class(c)

    def _clock_done(self, widget):
        self._block_exist = False
        self.set_keep_above(True)
        self.set_keep_above(False)
        if self._home_page:
            self._transition_home()
        else:
            self._new_home()
        #self.present()

    def _read_block(self):
        with open("time_block.txt") as f:
            time_done_cfg = f.readline()
        time = datetime.fromisoformat(time_done_cfg)

    def _emit_time(self, action, time):
        self._block_exist = True
        self.emit('save_block', time)
