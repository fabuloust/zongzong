#!/bin/sh
cd `dirname $0`

export PYTHONIOENCODING=utf-8:surrogateescape

# 直接访问默认virtualenv中的Python
if [ -f /root/workspace/ENV/bin/python ]; then
    /root/workspace/ENV/bin/python "$@"
elif [ -f ~/workspace/ENV/bin/python ]; then
    ~/workspace/ENV/bin/python "$@"
else
    python "$@"
fi
