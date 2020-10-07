desktop_file = i18n.merge_file(
  input: 'com.github.bunsenmurder.NoSurfin.desktop.in',
  output: 'NoSurfin.desktop',
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils,
    args: [desktop_file]
  )
endif

appstream_file = i18n.merge_file(
  input: 'com.github.bunsenmurder.NoSurfin.appdata.xml.in',
  output: 'com.github.bunsenmurder.NoSurfin.appdata.xml',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'appdata')
)

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
  test('Validate appstream file', appstream_util,
    args: ['validate', appstream_file]
  )
endif

compile_schemas = find_program('glib-compile-schemas', required: true)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()]
  )
endif

# PkExec Policy
conf_policy = configuration_data()
conf_policy.set('PYTHON', py_install.path())
conf_policy.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'com.github.bunsenmurder.NoSurfin.policy.in',
  output: 'com.github.bunsenmurder.NoSurfin.policy',
  configuration: conf_policy,
  install: true,
  install_dir: join_paths(get_option('datadir'), 'polkit-1/actions')
)
# GSchema Settings
install_data('com.github.bunsenmurder.NoSurfin.gschema.xml',
  install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)
# DBus Service Security
install_data('com.github.bunsenmurder.NSUrlManager.conf',
  install_dir: join_paths(get_option('datadir'), 'dbus-1/system.d')
)
