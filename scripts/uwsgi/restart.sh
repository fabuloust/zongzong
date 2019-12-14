#!/bin/sh

if [ $(ps -fe | grep "`pwd`/uwsgi.ini" | grep -v grep | wc -l) -eq 0 ]; then
sh `pwd`/scripts/uwsgi/start.sh
else
touchfile="`pwd`/scripts/uwsgi/touch_reload_uwsgi"
touch ${touchfile}
fi