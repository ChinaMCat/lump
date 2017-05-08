# -*- coding: utf-8 -*-

__version__ = "0.9"
__author__ = 'minamoto'
__doc__ = 'useful sql func'

import _mysql as mysql
import Queue


class MXMariadb(object):

    def __init__(self,
                 host='127.0.0.1',
                 port=3006,
                 user='root',
                 pwd='1234',
                 conv={1: int,
                       2: int,
                       3: int,
                       4: float,
                       5: float,
                       8: int,
                       9: int},
                 flag=32 | 65536 | 131072,
                 maxconn=20):
        """mariadb访问类初始化
        Args:    
            host: mariadb服务器名
            port: mariadb服务端口
            user: mariradb访问用户名
            pwd:  mariadb访问密码
            conv: 字段类型自动转换设置
            flag: 客户端访问标记,默认压缩,允许多语句提交,允许多结果集
        """
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.conv = conv
        self.flag = flag
        self.conn_queue = Queue.Queue(20)
        self.error_msg = ''
        self.show_debug = False

    def __del__(self):
        while self.conn_queue.qsize() > 0:
            cn = self.conn_queue.get_nowait()
            cn.close()
            del cn

    def get_conn(self):
        try:
            return self.conn_queue.get_nowait()
        except:
            try:
                cn = mysql.connect(host=self.host,
                                   port=self.port,
                                   user=self.user,
                                   passwd=self.pwd,
                                   conv=self.conv,
                                   client_flag=self.flag,
                                   connect_timeout=7)
                cn.set_character_set('utf8')
            except Exception as ex:
                self.error_msg = '_mysql conn error: {0}'.format(ex)
                if self.show_debug:
                    print(self.error_msg)
                return None
            else:
                return cn

    def put_conn(self, conn):
        try:
            self.conn_queue.put_nowait(conn)
        except:
            pass

    def run_fetch(self, strsql):
        '''数据库访问方法，
            用于执行select类语句
        Return:
            结果集的迭代器'''
        if len(strsql) == 0:
            yield None
        else:
            conn = self.get_conn()
            if conn is None:
                yield None
            else:
                try:
                    conn.query(strsql)
                except Exception as ex:
                    self.error_msg = '_mysql fetch error: {0}'.format(ex)
                    if self.show_debug:
                        print(self.error_msg)
                else:
                    cur = conn.use_result()
                    if cur is not None:
                        while True:
                            d = cur.fetch_row(619)
                            if len(d) == 0:
                                break
                            else:
                                for i in d:
                                    yield i
                    else:
                        yield None
                    del cur
                self.put_conn(conn)

    def run_exec(self, strsql):
        '''数据库访问方法
            用于执行delet，insert，update语句，支持多条语句一起提交，用‘;’分割
            Return:
            [(affected_rows,insert_id),...]'''
        if len(strsql) == 0:
            return None
        conn = self.get_conn()
        if conn is None:
            return None
        x = []
        try:
            conn.query(strsql)
        except Exception as ex:
            self.error_msg = '_mysql exec error: {0}'.format(ex)
            if self.show_debug:
                print(self.error_msg)
        else:
            conn.use_result()
            x.append((conn.affected_rows(), conn.insert_id()))
            while conn.next_result() > -1:
                x.append((conn.affected_rows(), conn.insert_id()))

        self.put_conn(conn)
        return x

    def get_last_error_message(self):
        return self.error_msg

    def set_debug(self, debug):
        self.show_debug = debug
        