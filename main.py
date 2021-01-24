import json
import math
import os
import platform
import random
import sqlite3
from time import sleep, time
from zlib import crc32

import requests as req

import assistances

headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36',
    'Referer': 'https://www.bilibili.com/'
}

def get_reply_raw(oid, type_, pn, root=None, sort=0):
    url_start = 'https://api.bilibili.com/x/v2/reply'
    if isinstance(root, int):
        url_start += '/reply'
    elif root is None:
        pass
    else:
        raise BaseException('root属性不正确!')
    resp = req.get(url_start, params={'oid':oid, 'root':root, 'pn':pn, 'type':type_, 'sort':sort}, headers=headers)
    if resp.status_code != 200:
        return {'status':resp.status_code, 'content':None}
    else:
        return {'status':resp.status_code, 'content':json.loads(resp.text)}

def get_reply_main(oid, oidtype, oidalias, cursor, root=None, database=None):            # 获取主楼，楼中楼递归调用即可
    page_max = 1
    count = 1
    reply_container = []
    while True:
        sleep(random.random() * 1.5)
        response = get_reply_raw(oid, oidtype, count, root=root)
        events = []
        # print(response)

        if response['status'] != 200:
            print(f'状态异常，编码为{response["status"]}')
            sleeptime = random.random() * 15
            print(f'程序休眠{sleeptime}秒后继续')
            ltimestamp = int(time())
            lastactivetime = assistances.time_stamp(ltimestamp)
            sql = '''INSERT INTO logs(oid, alias, type, status, roots, replies, timestamp, time, events) ''' + assistances.sql_values(
                oid, oidalias, oidtype, 'ERROR', -1, -1, ltimestamp, lastactivetime, str(response["status"]))
            cursor.execute(sql)
            sleep(sleeptime)
            continue
        else:
            pre_content = response['content']
            data = pre_content['data']
            current_page = data['page']['num']
            current_size = data['page']['size']
            current_count = data['page']['count']
            current_acount = data['page']['acount'] if root is None else None
            # print(current_page, current_size, current_count, current_acount)
            
            page_max = math.ceil(current_count/current_size)

            replies = data['replies'] if data['replies'] else []
            for reply in replies:
                rpid = reply['rpid']
                _root = reply['root'] if reply['root'] else None          # 如果root是零直接置空，否则取root
                parent = reply['parent'] if reply['parent'] else None    # 如果parent是零直接置空，否则取parent
                uname = reply['member']['uname']
                mid = reply['member']['mid']
                avatar = reply['member']['avatar']
                level = reply['member']['level_info']['current_level']

                content = reply['content']['message']
                crc32_value = '%08X' % crc32(bytearray(content, encoding='UTF-8'))
                device = reply['content']['device']
                rtimestamp = reply['ctime']
                replytime = assistances.time_stamp(rtimestamp)
                ltimestamp = int(time())
                lastactivetime = assistances.time_stamp(ltimestamp)
                uplike = reply['up_action']['like']
                upreply = reply['up_action']['reply']

                marks = []
                if uplike:
                    marks.append('UPLike')
                if upreply:
                    marks.append('UPReply')
                if rpid not in reply_container:
                    reply_container.append(rpid)
                else:
                    marks.append('DoubleHit')
                    events.append('DoubleHit')

                sql = '''SELECT rpid, content, crc32, Replytime FROM replies WHERE rpid = ? and oid = ? and type = ?;'''
                cursor.execute(sql, (rpid, oid, oidtype))
                results = cursor.fetchall()
                same_counts=0
                for i in results:
                    if content == i[1] and crc32_value == i[2]:
                        same_counts += 1
                    else:
                        marks.append('CRC32ERR')
                        events.append('CRC32ERR')

                if same_counts:
                    sql = '''UPDATE replies SET lastactivetime = ?, ltimestamp = ? WHERE rpid = ? and oid = ? and type = ?;'''
                    cursor.execute(sql, (lastactivetime, ltimestamp, rpid, oid, oidtype))
                else:
                    sql = '''INSERT INTO replies(oid, type, alias, rpid, root,
                        parent, uname, mid, content,
                        device, replytime, rtimestamp,
                        lastactivetime, ltimestamp, crc32, marks) ''' + \
                        assistances.sql_values(oid, oidtype, oidalias, rpid, _root,
                        parent, uname, mid, content,
                        device, replytime, rtimestamp,
                        lastactivetime, ltimestamp, crc32_value, str(','.join(marks)))
                    # print(sql)
                    cursor.execute(sql)

                sql = '''SELECT mid, uname, level, avatar FROM users WHERE mid = ?;'''
                cursor.execute(sql, (mid,))
                results = cursor.fetchall()
                same_counts = 0
                for i in results:
                    if i[1] == uname and i[2] == level and i[3] == avatar:
                        same_counts += 1
                if same_counts:
                    sql = '''UPDATE users SET recordtime = ?, rtimestamp = ? WHERE mid = ? and uname = ? and level = ? and avatar = ?;'''
                    cursor.execute(sql, (lastactivetime, ltimestamp, mid, uname, level, avatar))
                else:
                    sql = '''INSERT INTO users(mid, uname, level, avatar, recordtime, rtimestamp) ''' + assistances.sql_values(
                        mid, uname, level, avatar, lastactivetime, ltimestamp)
                    cursor.execute(sql)

                if reply['replies'] != None:
                    get_reply_main(oid=oid, oidtype=oidtype, oidalias=oidalias, cursor=cursor, root=rpid, database=database)
            
            
            if count == 1:
                events.append('HEAD')
            if count == page_max:
                events.append('TAIL')
            if current_acount is None:
                events.append('DEEP')

            sql = '''INSERT INTO logs(oid, alias, type, root, status, roots, replies, current_pagecount, timestamp, time, events) ''' + assistances.sql_values(
                oid, oidalias, oidtype, root, 'PASSED', current_count, current_acount, current_page, ltimestamp, lastactivetime, str(','.join(events)))
            cursor.execute(sql)
        
        if database:
            database.commit()

        # print(count, '/', page_max, events)
        if count >= page_max:
            break
        else:
            count += 1


