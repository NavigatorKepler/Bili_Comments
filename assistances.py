import csv
import json
import sqlite3
from random import random
from time import localtime, sleep, strftime

import requests as req

# 评论表 oid, type, rpid, root, parent, uname, mid, content, device, replytime, rtimestamp,
#              lastactivetime, ltimestamp, crc32, marks(CRC32ERR, UPLike, UPReply)
# 日志表 oid, alias, status, roots, replies, timestamp, time, events(ObviousDelete, DoubleHit, CRC32ERR, HEAD, TAIL)
# 用户表 mid, uname, level, avatar, recordtime, rtimestamp

def sql_init(cursor):
    sql = '''CREATE TABLE IF NOT EXISTS logs(
    oid        INT,  alias      TEXT,  type                INT,
    root       INT,  status     TEXT,
    roots      INT,  replies    INT,   current_pagecount   INT,
    timestamp  INT,  time       TEXT,  events             TEXT);'''
    cursor.execute(sql)
    sql = '''CREATE TABLE IF NOT EXISTS users(
    mid        INT,  uname      TEXT, level     INT,
    avatar     TEXT, recordtime INT,  rtimestamp INT);'''
    cursor.execute(sql)
    sql = '''CREATE TABLE IF NOT EXISTS replies(
    oid        INT,  alias      TEXT, type       INT,
    rpid       INT,  root       INT,  parent     INT,
    uname      TEXT, mid        TEXT,
    content    TEXT, device     TEXT, crc32      TEXT,
    replytime  TEXT, rtimestamp INT,
    lastactivetime TEXT, ltimestamp INT, marks      TEXT);'''
    cursor.execute(sql)

def sql_connect(sqlfile='database.db'):
    database = sqlite3.connect(sqlfile)
    cursor = database.cursor()
    sql_init(cursor)
    database.commit()
    return database, cursor

def time_stamp(*args):              # 将时间戳转换为日期
    timestamp = args[0] if args else None
    time = str(strftime('%Y', localtime(timestamp)) + '年' +
               strftime('%m', localtime(timestamp)) + '月' +
               strftime('%d', localtime(timestamp)) + '日' +
               strftime('%H', localtime(timestamp)) + '时' +
               strftime('%M', localtime(timestamp)) + '分' +
               strftime('%S', localtime(timestamp)) + '秒')
    return time

def sql_values(*args):              # 用于组合VALUES语句
    basic = 'VALUES ('
    hashead = False
    for i in args:
        if hashead == True:
            basic += ', '
        hashead = True
        if i == None:
            basic += 'NULL '
        elif isinstance(i, int):
            basic += str(i)+' '
        else:
            # i = i.replace('\\', '\\\\')
            i = i.replace('\'', '\'\'')
            basic += '\'' + str(i) + '\''
    basic += ');'
    return basic

def csv_loader(file='config.csv'):
    targets = []
    with open(file, encoding='UTF-8') as f:
        f_csv = csv.reader(f)
        f_items = []
        for i in f_csv:
            items = []
            for j in i:
                items.append(j.strip())
            f_items.append(items)

        # return f_items
        if len(f_items) <= 1:
            raise BaseException('目标配置错误!')

        try:
            replies_oid_col = f_items[0].index('replies_oid')
            type_col = f_items[0].index('type')
            alias_col = None if f_items[0] == 2 else f_items[0].index('alias')
        except:
            raise BaseException('找不到对应列!')

        for i in range(1, len(f_items)):
            if f_items[i][replies_oid_col] and f_items[i][type_col]:
                targets.append({
                    'oid':f_items[i][replies_oid_col],
                    'type':f_items[i][type_col],
                    'alias':None if alias_col is None else f_items[i][alias_col]
                })

    return targets
