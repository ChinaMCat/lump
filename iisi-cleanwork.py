#!/usr/bin/env python
# coding: utf-8

import urllib2

url = 'http://127.0.0.1:{0}/cleaningwork'

if __name__ == '__main__':
    f = open('wsport.list', 'r')
    x = f.readline()
    f.close()
    pp = x.split(',')
    for p in pp:
        try:
            urllib2.urlopen(url.format(int(p)), timeout=1)
        except Exception as ex:
            print(ex)
