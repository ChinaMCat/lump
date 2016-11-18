#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '0.1'
__doc__ = 'cxsetup_tcs_sl.py'

import glob
import os

if  __name__ == '__main__':
    # os.system('rm -f *.pyc')
    os.system('cp ../protobuf2/*.proto .')
    files = glob.glob('*.proto')
    for ff in files:
        print('sed', ff)
        os.system('sed -i.bak -e "1,2s/proto2/proto3/g" -e "s/optional //g" {0}'.format(ff))
    os.system('protoc --python_out=. *.proto')
    os.system('rm *.bak')
