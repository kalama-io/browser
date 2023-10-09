#!/bin/sh

/usr/bin/su $USER -c  "/usr/sbin/installer -pkg ./kalama_browser_package.pkg -target CurrentUserHomeDirectory"

exit 0
