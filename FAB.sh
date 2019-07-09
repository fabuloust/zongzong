#!/bin/sh
#!/bin/sh
# 直接访问默认virtualenv中的fab
if [ -f /home/chunyu/workspace/ENV/bin/fab ]; then
    /home/chunyu/workspace/ENV/bin/fab "$@"
elif [ -f ~/workspace/ENV/bin/fab ]; then
    ~/workspace/ENV/bin/fab "$@"
else
    fab "$@"
fi
