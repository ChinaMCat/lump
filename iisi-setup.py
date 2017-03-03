#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import uuid
import sys
import platform
from mxpsu import showOurHistory, SCRIPT_DIR, stamp2time

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'pytcs-setup.py'

osinfo = platform.dist()
if "ubuntu" in osinfo[0].lower():
    pkgfile = "imps.x86_64-linux-gnu.so"
else:
    pkgfile = "_imps.so"

zh = {"root": u"安装程序需要root权限，安装过程中止。",
      "path": u"请输入安装路径，默认安装在 '/opt/dclms'（留空使用默认目录）:",
      "start_i": u"安装正在进行，请稍候...",
      "end_i": u"安装完成，输入 'iisi' 运行程序。",
      "start_u": u"升级正在进行，请稍候...",
      "end_u": u"升级完成。",
      "is_autostart": u"\r\n是否将服务设置为自动启动？（默认不设置）[y/n]",
      "autostart_port": u"请输入自动监听端口号：",
      "port_err": u"端口号非法！"}

en = {
    "root": u"This program must be run as root. Aborting.",
    "path":
    u"Please enter the installation path, the default is '/opt/dclms' (just press Enter to use the default directory):",
    "start_i": u"Installation is in progress, please wait...",
    "end_i": u"Installation is complete, type 'iisi' to run the program.",
    "start_u": u"Upgrade is in progress, please wait...",
    "end_u": u"Upgrade is complete.",
    "is_autostart":
    u"\r\nDo you want to set the service to start automatically? [y/n] (default is 'n')",
    "autostart_port": u"Please enter the listening port:",
    "port_err": u"Port number is wrong!"
}

autostart = """[Unit]
Description=(Terminal communication services) vb6 compatible version
After=network.target

[Service]
ExecStart=/usr/bin/screen -dmS tcs{0} /usr/local/bin/tcs --port={0}
ExecReload=/bin/kill $MAINPID
# supress to log debug and error output also to /var/log/messages
Type=oneshot
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""

if __name__ == "__main__":
    if os.geteuid():
        print('input root password.')
        x = sys.path[0]
        if os.path.isdir(x):
            args = [sys.executable] + sys.argv
        elif os.path.isfile(x):
            args = sys.argv
        os.execlp('su', 'su', '-c', ' '.join(args))

    update = False
    if "history" in sys.argv or "--history" in sys.argv:
        showOurHistory()
        sys.exit(0)
    arg = argparse.ArgumentParser(add_help=True)

    # arg.add_argument('--upgrade',
    #                  action='store_true',
    #                  dest='upgrade',
    #                  default=False,
    #                  help='Just upgrade modules, not install the whole program.')
    arg.add_argument('--zh',
                     action='store_true',
                     dest='zh',
                     default=False,
                     help='Show Chinese text.')

    arg.add_argument('--version',
                     action='version',
                     version=u'{0} {1} v{2}'.format('%(prog)s', __doc__, __ver__))
    results = arg.parse_args()

    if results.zh:
        showtext = zh
    else:
        showtext = en

    defaultpath = os.path.join("/", "opt")
    username = os.getlogin()
    # homepath = os.path.join("/", "home", username)
    if os.getuid() != 0:
        print(showtext["root"])
        sys.exit(1)

    x = uuid.uuid1()
    os.system("mkdir -p /tmp/{0}".format(x))
    if True:
        # print(showtext["path"])
        # p = raw_input("")
        # if len(p) == 0:
        p = os.path.join(defaultpath, "dclms")
        # else:
        #     p = os.path.join(p, "dclms")

        print(showtext["start_i"])
        os.system("tar -Jxvf {1}/{2} -C /tmp/{0}/ > /tmp/.0".format(x, SCRIPT_DIR, pkgfile))
        # os.system("7z x -y -plkjfdsa -o/tmp/{0}/ {1}/{2} > /tmp/0".format(x, SCRIPT_DIR, pkgfile))
        t = stamp2time(os.path.getmtime(r"/tmp/{0}/iisi/iisi".format(x)), format_type="%y%m%d")

        s = """#!/bin/bash
mkdir -p {0}/iisi{3}
cp -rf /tmp/{1}/iisi/* {0}/iisi{3}/

mkdir -p /etc/dclms

chmod +x {0}/iisi{3}/iisi
ln -sf {0}/iisi{3}/iisi /usr/local/bin/iisi
ln -sf {0}/iisi{3}/iisi /usr/bin/iisi
ln -sf {0}/iisi{3}/zmqproxy /usr/local/bin/zmqproxy
ln -sf {0}/iisi{3}/zmqproxy /usr/bin/zmqproxy
    """.format(p, x, username, t)
        with open("/tmp/{0}/tmp.sh".format(x), "w") as f:
            f.write(s)
        os.system("chmod +x /tmp/{0}/tmp.sh".format(x))
        os.system("chmod a+rx /tmp/{0}".format(x))
        os.system("/tmp/{0}/tmp.sh".format(x))
        print(showtext["end_i"])
        # if 'centos' in osinfo[0].lower() and int(osinfo[1][0]) >= 7:
        #     print(showtext["is_autostart"])
        #     g = raw_input("")
        #     if g.lower().startswith('y'):
        #         print(showtext["autostart_port"])
        #         p = raw_input("")
        #         try:
        #             z = int(p)
        #             if 1000 < z < 65535:
        #                 with open("/tmp/{0}/tcs{1}.service".format(x, z), "w") as f:
        #                     f.write(autostart.format(z))
        #                 os.system("sudo cp /tmp/{0}/tcs{1}.service /etc/systemd/system/".format(x, z))
        #                 os.system("sudo systemctl daemon-reload;systemctl enable tcs{0}".format(z))
        #                 # with open("/tmp/{0}/tcs{1}".format(x, z), "w") as f:
        #                 #     f.write(autostart.format(z))
        #                 # os.system("cp /tmp/{0}/tcs{1} /etc/init.d/".format(x, z))
        #                 # os.system("chmod +x /etc/init.d/tcs{0}".format(z))
        #                 # os.system("ln -s -f /etc/init.d/tcs{0} /etc/rc2.d/S99tcs{0}".format(z))
        #             else:
        #                 print(showtext["port_err"])
        #         except Exception as ex:
        #             print(ex.message)
        os.system("rm -rf /tmp/{0}".format(x))
        os.system("rm -f /tmp/0")
    else:
        print(showtext["start_u"])
        os.system("tar -Jxvf {1}/{2} -C /tmp/{0}/ > /tmp/0".format(x, SCRIPT_DIR, pkgfile))
        # os.system("7z x -y -plkjfdsa -o/tmp/{0}/ {1}/{2} > /tmp/0".format(x, SCRIPT_DIR, pkgfile))

        s = """#!/bin/bash
mkdir -p /usr/lib64/python2.7/site-packages/dpv4
mkdir -p /usr/lib64/python2.7/site-packages/protobuf3

cp -rf /tmp/{1}/google/ /usr/lib64/python2.7/site-packages/
cp -f /tmp/{1}/dpv4/*.pyc /usr/lib64/python2.7/site-packages/dpv4/
cp -f /tmp/{1}/protobuf3/*.pyc /usr/lib64/python2.7/site-packages/protobuf3/
find /usr/lib64/python2.7/site-packages/dpv4 -name "*.py" | xargs rm -vf
find /usr/lib64/python2.7/site-packages/protobuf3 -name "*.py" | xargs rm -vf
mkdir -p /etc/dclms
rm -rf /var/cache/dclms/tcs.d/tcs-updated-*
    """.format("", x)
        with open("/tmp/{0}/tmp.sh".format(x), "w") as f:
            f.write(s)
        os.system("chmod +x /tmp/{0}/tmp.sh".format(x))
        os.system("chmod a+rx /tmp/{0}".format(x))
        os.system("/tmp/{0}/tmp.sh".format(x))
        print(showtext["end_u"])
        os.system("rm -rf /tmp/{0}".format(x))
        os.system("rm -f /tmp/0")
