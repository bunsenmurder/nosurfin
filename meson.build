project('nosurfin', 'c',
          version: '0.5.0',
    meson_version: '>= 0.50.0',
  default_options: ['c_std=c99',
  		    'warning_level=2']
)
# Find and set up c compiler
cc = meson.get_compiler('c')
cflags = cc.get_supported_arguments(['-O2'])
add_project_arguments(cflags, language: 'c')

#Set variables
prefix = get_option('prefix')
meson_version_split = meson.version().split('.')
#pkgdatadir = '/usr/local/share/nosurfin' or '/usr/share/nosurfin'
pkgdatadir = join_paths(prefix, get_option('datadir'), meson.project_name())
#glib_req = '>= 2.60.0'

# Find run time and system dependencies
#python_dep = dependency('python3', version: '>= 3.6')
gio_dep = dependency('gio-2.0')
gio_unix_dep = dependency('gio-unix-2.0')
glib_dep = dependency('glib-2.0')
gtk_dep = dependency('gtk+-3.0', version: '>= 3.24.0')


# Import Libraries
i18n = import('i18n') # Localization
gnome = import('gnome')
python = import('python')
py_install = python.find_installation('python3')

# Find python libraries
#if meson_version_split[1].to_int() >= 51
	
	#		modules: ['mitmproxy'])
	# Please ensure jeepney is installed if you wish add urls to block
#else
#	py_install = python.find_installation('python3')
	#message('Please ensure mitmproxy is installed and version >= 5.1')
	#message('Please ensure jeepney is installed and version >= 0.4')
#endif

# Include sub-directories
subdir('data')
subdir('nosurfin')
subdir('po')

#Post Install Script
meson.add_install_script('build-aux/meson/postinstall.py')
