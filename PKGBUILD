pkgname=nosurfin
pkgver=0.3.0
pkgrel=1
pkgdesc="Website blocker capable of blocking specific URLs"
url="https://github.com/bunsenmurder/nosurfin"
arch=('any')
license=('GPL3')
depends=(python-gobject mitmproxy iptables gtk3)
makedepends=(glib2 git meson appstream-glib python)
source=("git+https://github.com/bunsenmurder/nosurfin.git")
sha256sums=('SKIP')

pkgver() {
  cd $pkgname
  git describe --tags | sed 's/v//g'
}

prepare() {
  cd $pkgname
}

build() {
  arch-meson $pkgname build
  ninja -C build
}

package() {
  DESTDIR="$pkgdir" ninja -C build install
}
