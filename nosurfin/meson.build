#moduledir = '/usr/local/share/nosurfin/nosurfin' ir '/usr/share/nosurfin/nosurfin'
moduledir = join_paths(pkgdatadir, 'nosurfin')
pkglibdir = join_paths(prefix, get_option('libdir'), 'nosurfin')

url_manager_dep = [
  gio_dep,
  gio_unix_dep,
  glib_dep
]

codegen = gnome.gdbus_codegen('nsurlmanager',
  'url-manager/com.github.bunsenmurder.NSUrlManager.xml',
  interface_prefix: 'com.github.bunsenmurder'
)

url_manager_sources = [
  'url-manager/nsurlmanager-main.c',
  codegen
]

executable ('nsurlmanager',
  url_manager_sources,
  dependencies: url_manager_dep,
  install: true,
  install_dir: pkglibdir,
  install_rpath: pkglibdir
)

gnome.compile_resources('nosurfin',
  'nosurfin.gresource.xml',
  gresource_bundle: true,
  source_dir: meson.current_build_dir(),
  install: true,
  install_dir: pkgdatadir
)

conf = configuration_data()
conf.set('PYTHON', py_install.path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'nosurfin.in',
  output: 'nosurfin',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

nosurfin_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'clock.py',
  'home.py',
  'dbus_tools.py',
  'editor.py',
  'preferences.py',
  'misc.py',
  'wizard.py'
]

install_data(nosurfin_sources, install_dir: moduledir)
install_subdir('nosurfin.d', install_dir: moduledir)
