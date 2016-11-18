#!/usr/bin/env python
# -*- coding: utf-8 -*-


from Crypto.Hash import MD5
import sys


def hashMD5(str):
    m = MD5.new()
    m.update(str)
    return m.hexdigest()


if __name__ == "__main__":
    print(hashMD5(str(sys.argv[1])))