#!/bin/sh

uwsgifile="`pwd`/uwsgi.ini"
touchfile="`pwd`/scripts/uwsgi/touch_reload_uwsgi"
touchlogfile="`pwd`/scripts/uwsgi/touch_reopen_log"

PWD=`pwd`
source ${PWD}/scripts/_common.sh


# 搜索默认的路径
UWSGI_PATH="${ENV_PATH}/bin/uwsgi"

# 使用指定账号启动服务
${UWSGI_PATH} --uid zongzong --ini ${uwsgifile} --touch-reload=${touchfile} --touch-logreopen=${touchlogfile}

