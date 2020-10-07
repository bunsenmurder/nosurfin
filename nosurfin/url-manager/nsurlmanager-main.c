// nsurlmanager-main.c
//
// Copyright 2020 bunsenmurder
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

#include <stdio.h>
#include "nsurlmanager.h"
#include <glib.h>

static GMainLoop *loop;

static void on_name_acquired_cb(GDBusConnection *connection,
                             const gchar *name,
                             gpointer user_data)
{
    NSUrlManager *url_manager = nsurl_manager_skeleton_new();

    g_dbus_interface_skeleton_export(G_DBUS_INTERFACE_SKELETON(url_manager),
                                     connection,
                                     "/com/github/bunsenmurder/NSUrlManager",
                                     NULL);

}

int main (void)
{
    gchar *name;
    name = "com.github.bunsenmurder.NSUrlManager";
    guint owner_id = g_bus_own_name(G_BUS_TYPE_SYSTEM,
                                    name,
                                    G_BUS_NAME_OWNER_FLAGS_NONE,
                                    NULL,
                                    &on_name_acquired_cb,
                                    NULL,
                                    NULL,
                                    NULL);
    loop = g_main_loop_new(NULL, FALSE);
    g_main_loop_run(loop);
    g_bus_unown_name(owner_id);
    return 0;
}
