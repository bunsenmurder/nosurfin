# gasync.py
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

from gi.repository import Gio

## API wrapper to use GTask/Gio.Task api for running asynchronous tasks.
## gasync_task is the decorator for the function you want to run asynchronously.
## run_gasync_task runs the function decorated with a gasync_task decorator.
## References
#https://lazka.github.io/pgi-docs/index.html#Gio-2.0/classes/Task.html#Gio.Task
#https://developer.gnome.org/gio/stable/GTask.html
#https://discourse.gnome.org/t/how-to-return-value-in-gio-task/3455/4

def run_gasync_task(func, func_cb):
    """ Runs a gasync_task. Only keyword args can be passed to functions, which
    is done using the partial function from the functools module. Check out the
    route_cb function in the wizard.py file for example usage.

    :param Callable func: Function decorated with gasync_task decorator.
    :param Callable func_cb: Callback function to call after async task is done.
    """
    # Returns the results from asynchronous task
    def gasync_return(obj, pointer, callback):
        success, res = pointer.propagate_value()
        if success:
            callback(res)
    task = Gio.Task.new(None, None, gasync_return, func_cb)
    # Runs task asynchronously in another thread
    task.run_in_thread(func)

def gasync_task(method=False):
    """ Decorator for the function to be run asynchronously.
    :param bool method: Toggle true if function is an instance method.
    """
    def decorate(func):
        def _method(self, task, *args, **kwargs):
            res = func(self, **kwargs)
            task.return_value(res)
        def _function(task, *args, **kwargs):
            res = func(**kwargs)
            task.return_value(res)
        if method:
            return _method
        else:
            return _function
    return decorate
