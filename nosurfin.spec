Name:           nosurfin
Version:        0.5.0
Release:        1%{?dist}
Summary:        Personal Website Blocker

License:        GPLv3+
URL:            https://github.com/bunsenmurder/nosurfin
Source0:        https://github.com/bunsenmurder/%{name}/archive/%{name}-%{version}.tar.gz

BuildRequires:  python3-gobject
BuildRequires:  python3-gobject-devel
BuildRequires:  meson >= 0.50.0
BuildRequires:  gobject-introspection
BuildRequires:  glib2-devel
BuildRequires:  cmake
BuildRequires:  gtk3-devel

Requires:       python3-gobject >= 3.36.0
Requires:       pipx
Requires:       gobject-introspection
Requires:       nss-tools
Requires:       systemd
Requires:       gtk3

%description
Block distracting websites and take back your productivity! NoSurfin is a personal web site blocker for Linux, capable of blocking specific URLs instead of just website hosts. Just add the URLs you wish to block to the block list, set the time period, and activate the block; those websites will be blocked until the timer finishes. Great for when you want to stop surfing the web and get some work done!

%prep
%autosetup


%build
%meson
%meson_build


%install
%meson_install


%files
%license LICENSE
%{_bindir}/nosurfin
%{_datadir}/nosurfin
%{_libdir}/nosurfin/nsurlmanager
%{_datadir}/applications/NoSurfin.desktop
%{_datadir}/appdata/com.github.bunsenmurder.NoSurfin.appdata.xml
%{_datadir}/polkit-1/actions/com.github.bunsenmurder.NoSurfin.policy
%{_datadir}/dbus-1/system.d/com.github.bunsenmurder.NSUrlManager.conf
%{_datadir}/glib-2.0/schemas/com.github.bunsenmurder.NoSurfin.gschema.xml
/usr/lib/debug/usr/lib64/nosurfin/nsurlmanager-0.5.0-1.fc32.x86_64.debug


%changelog
* Fri Oct  9 2020 bunsenmurder
- Changelog can be found here: https://github.com/bunsenmurder/nosurfin
