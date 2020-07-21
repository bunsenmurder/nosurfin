pkgname=nosurfin
pkgver=0.2.0
pkgrel=1
pkgdesc="Block distracting websites and take back your productivity"
url="https://github.com/bunsenmurder/nosurfin"
arch=('any')
license=('GPL3')
depends=(python-gobject mitmproxy iptables)
makedepends=(gobject-introspection git meson appstream-glib python)
source=("git+https://github.com/bunsenmurder/nosurfin.git")
sha256sums=('SKIP')

prepare() {
  cd nosurfin
  git submodule init
  git submodule update
}

build() {
  arch-meson nosurfin build
  ninja -C build
}

package() {
  DESTDIR="$pkgdir" ninja -C build install
}
