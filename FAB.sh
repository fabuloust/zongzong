#!/bin/sh
#!/bin/sh
# 直接访问默认virtualenv中的fab
if [ -f /Users/huxiaotian/zongzong/ENV/bin/fab ]; then
    /Users/huxiaotian/zongzong/ENV/bin/fab "$@"
elif [ -f ~/workspace/zongzong/ENV/bin/fab ]; then
    ~/workspace/ENV/bin/fab "$@"
else
    fab "$@"
fi
