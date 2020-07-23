## NoSurfin: Take back your productivity!

![nosurfin-main-screen][nosurfinimg]

Linux based website blocker capable of blocking whole websites or specific URLs. Great for when you need a break from surfing the web or getting some work done distraction-free!

Note: Has only been tested on Arch Linux and is still in production.

### Installing NoSurfin

``` 
mkdir nosurfin
cd nosurfin
curl https://raw.githubusercontent.com/bunsenmurder/nosurfin/master/PKGBUILD -o PKGBUILD
makepkg -si
cd src/nosurfin
chmod 755 cert_install.sh
sudo ./cert_install.sh
```

### Using NoSurfin

![nosurfin-menu][menu]

Note: You cannot add spaces to the URLs. You also must not add prefixes like www or https to the URL.

* **Block List** <br />
Here is where you define the websites or URLs you want to block. For example, if you wish to block Reddit, just add *reddit.com*. If you wanted to block a specific part of reddit but not all of you can add something like *reddit.com/r/popular* instead. You can also block specific keywords that might show up in a URL. For example, if you add the word *cat*, any URLS with the word cat in it will be blocked.

* **Ignore List** <br />
Here is where you specify only the website domains you wish to ignore. Meaning you can only specify *reddit.com* as *reddit.com/r/popular* or *cat*  **would not work**.  Since NoSurfin makes use of transparent proxying, it means that all websites will be filtered through the proxy which could have some hiccups depending on the site. I recommend adding your search engine to this list for best experience. Please note, that specific URL or keyword blocking will not work on sites listed here.

<!-- links -->
[nosurfinimg]:images/nosurfin.png
[menu]:images/nosurfin-menu.png