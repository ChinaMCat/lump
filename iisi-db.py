#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'minamoto'
__ver__ = '1.0.161111'
__doc__ = u'''交互式综合服务接口（Interactive Integrated Services Interface）'''

import time
import mxpsu as mx

def mysqlconnector():
    import mysql.connector as mysql
    a = time.time()
    conn = mysql.connect(
        host='192.168.50.83',
        port=3306,
        user='root',
        passwd='lp1234xy',
        # conv={1: int,
        #       2: int,
        #       3: int,
        #       4: float,
        #       5: float,
        #       8: int,
        #       9: int},
        # client_flag=32 | 65536 | 131072,
        connect_timeout=7)
    b = time.time()
    strsql = 'select a.*,b.* from mydb2024_data.data_rtu_record as a \
                left join mydb2024_data.data_rtu_loop_record as b \
                on a.date_create=b.date_create and a.rtu_id=b.rtu_id limit 1000'
    cur = conn.cursor()
    cur.execute(strsql)
    x = cur.fetchall()
    print(len(x))
    c = time.time()
    print(mx.stamp2time(a), mx.stamp2time(b), mx.stamp2time(c))
    print(c-b)

def mysqlc():
    import _mysql as mysql
    a = time.time()
    conn = mysql.connect(
        host='192.168.50.83',
        port=3306,
        user='root',
        passwd='lp1234xy',
        # conv={1: int,
        #       2: int,
        #       3: int,
        #       4: float,
        #       5: float,
        #       8: int,
        #       9: int},
        # client_flag=32 | 65536 | 131072,
        connect_timeout=7)
    b = time.time()
    strsql = 'select a.*,b.* from mydb2024_data.data_rtu_record as a \
                left join mydb2024_data.data_rtu_loop_record as b \
                on a.date_create=b.date_create and a.rtu_id=b.rtu_id limit 1000'
    conn.query(strsql)
    cur = conn.store_result()
    x = cur.fetch_row(0)
    print(len(x))
    c = time.time()
    print(mx.stamp2time(a), mx.stamp2time(b), mx.stamp2time(c))
    print(c-b)
i=0
def get_conn():
    global i
    i+=1
    if i<10:
        get_conn()
    return i

if __name__ == '__main__':
    a=get_conn()
    print(a)
