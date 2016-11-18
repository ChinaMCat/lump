#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = u'''mlib iisi'''

import os as _os
import codecs as _codecs

ConfData = {}


def loadConfigFile(filepath):
    global ConfData
    if _os.path.isfile(filepath):
        with _codecs.open(filepath, 'r', 'utf-8') as ff:
            lines = ff.readlines()
        for l in lines:
            if l.strip().startswith("#") or len(l.strip()) == 0:
                continue
            if l.find("=") > 0:
                a = l.split("=")[0].strip()
                if a in ConfData.keys():
                    v = l.split("=")[1].strip().replace(" ", "#")
                    ConfData[a] = v.split("#")[0]
        return ('ok: config file load success.', 20)
    else:
        return ('err: no config file `{0}` found.'.format(filepath), 40)
