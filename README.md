# NoSurfin: Take back your productivity!

![nosurfin-main-screen][nosurfinimg]

Block distracting websites and take back your productivity! NoSurfin is a personal website blocker for Linux, capable of blocking a specific URLs instead of just website hosts. Just add the URLs you wish to block to the block list, set the time period, and activate the block; those websites will be blocked until the timer finishes. Great for when you want to stop surfing the web and get some work done!

## Background
With so many sources of distraction on the internet and many websites being [designed to be addictive](https://getcoldturkey.com/blog/websites-addictive/). I found myself wasting too much time on the web which often times affected my productivity whenever I had work to do. Most existing solutions to this problem did not support Linux, and the ones that did were either inadequate or not being actively developed; NoSurfin was created in order to fill that gap. 

## How it Works
[Mitmproxy](https://mitmproxy.org/) is set up as a local transparent proxy, which all HTTP(s) traffic on the computer is filtered through. The NoSurfin plugin for Mitmproxy blocks all HTTP requests of matched URLs. This approach is used over hosts file blocking for two main reasons:

1. The traditional way of blocking websites uses [hosts file blocking](https://nordvpn.com/blog/use-hosts-file-block-ads-malware/), which prevents your computer from doing a DNS lookup of a website for it's IP. Sadly, this method of website blocking became obsolete with the advent of [DNS over HTTPS](https://en.wikipedia.org/wiki/DNS_over_HTTPS), which most web browsers come preinstalled with. 

2. The ability to block a specific URL path instead of the whole host. For example, if you only wanted to block *reddit.com/r/popular* but not the whole of Reddit. You would add *reddit.com/r/popular* to the block list and only that particular URL will be blocked while the rest of *reddit.com* will still be accessible.

## Installing

<u>Debian (>=11) / Ubuntu (>=20.04):</u>

_Note: Must install python-gi from unstable for Debian._

Download the DEB file from the Releases Section.

<u>Fedora (>=32):</u>

Download the RPM file from the Releases Section.

<u>Arch Linux:</u>

Open a terminal and run the commands below:

```
mkdir nosurfin && cd nosurfin && curl https://raw.githubusercontent.com/bunsenmurder/nosurfin/master/PKGBUILD -o PKGBUILD
makepkg -si

# Clean up files with
cd ..
rm -rf nosurfin
```

## Usage
![nosurfin-menu][menu]

### Block and Ignore Lists
These lists are for defining URL rules that control how the transparent proxy filters website traffic during a block. While a block is active, you add can unlimited entries to the block list and up to one entry to the ignore list.

* **Block List** <br />
Define URLs you wish to block in this list. Entries should be entered as described in the <b>How it Works</b> [2.] section above. You can also block specific keywords within a URL; for example, if you add the word *cat* to the block list, any URLS with the word cat in it will be blocked. Please note that you must remove prefixes like _www_ or _https_ from the URL. 

* **Ignore List** <br />
This list is for specifying a website which you do not want being routed through the proxy, best used for sites (e.g. search engines, etc.) that don't work well with Mimtproxy. When adding entries to this list you should not specify a specific URL but only the host of the URL. For example, you cannot specify *reddit.com/r/popular* to ignore and must only specify it's hosts *reddit.com*. You also cannot add keywords to this list like with the block list.


### The Certificate Wizard
The Certificate Wizard is a built-in utility that helps you manage program and system certificate stores that you install the Mitmproxy SSL certificate to. It can be opened from preferences and provides three options:
![nosurfin-certificate-wizard][certwiz]

* **General Certificate Install** <br />
Installs the SSL certificate to the system cert store. You are prompted to install this on startup, you won't need to use this much unless you say no at startup certificate check.

* **Install Certificate to Apps** <br />
Applications that do not use the System Certificate store will not connect to the internet while a block is active; use this option to install the SSL certificate to their individual certificate stores. Currently supports NSS databases and PEM cert bundles.

* **Remove Installed Certificates** <br />
Use this option to remove the SSL certificate from the system and any apps which it was installed to. Please note that the system certificate entry will be hidden while a block is active.

<!-- links -->
[nosurfinimg]:images/nosurfin.png
[menu]:images/nosurfin-menu.png
[pref]:images/nosurfin-preferences.png
[certwiz]:images/nosurfin-cert-wiz.png