# Maintainer: bunsenmurder <bunsenmurder@disroot.org>
_pkgname=nosurfin
pkgname="$_pkgname"-git
pkgver=0.5.0
pkgrel=1
pkgdesc="Block distracting websites and take back your productivity!"
url="https://github.com/bunsenmurder/nosurfin"
arch=('any')
license=('GPL3')
depends=(gtk3 mitmproxy python-gobject python-jeepney systemd nss)
makedepends=(appstream-glib git meson python)
source=("git+https://github.com/bunsenmurder/nosurfin.git")
sha256sums=('SKIP')

pkgver() {
  cd $_pkgname
  git describe --long --tags | sed 's/^v//;s/\([^-]*-g\)/r\1/;s/-/./g'
}

build() {
  arch-meson $_pkgname build
  ninja -C build
}

package() {
  DESTDIR="$pkgdir" ninja -C build install
}
