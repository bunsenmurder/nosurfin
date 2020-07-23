#pkgdatadir = '/usr/local/share/nosurfin'
#moduledir = '/usr/local/share/nosurfin/nosurfin'
pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'nosurfin')
gnome = import('gnome')

gnome.compile_resources('nosurfin',
  'nosurfin.gresource.xml',
  gresource_bundle: true,
  source_dir: meson.current_build_dir(),
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
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
  'sleep.py',
  'editor.py',
]

install_data(nosurfin_sources, install_dir: moduledir)
install_subdir('nosurfin.d', install_dir: moduledir)
