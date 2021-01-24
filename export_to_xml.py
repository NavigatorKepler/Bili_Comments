# 显示的参数 oid type alias // nickname uid level replytime lastactivetime content replies
import sqlite3
import xmltodict

import assistances

if __name__ == '__main__':
    targets = assistances.csv_loader()
    d,c = assistances.sql_connect()
    root = {'xml_content':{}}
    for i in targets:

        temp_dict = {
            'oid':i['oid'],
            'type':i['type'],
            'alias':i['alias'],
            'replies':{}
        }

        sql = '''SELECT rpid, root, uname, mid, replytime, lastactivetime, content FROM replies WHERE oid = ? and type = ?'''
        c.execute(sql, (i['oid'], i['type']))
        replies = c.fetchall()
        stat = False    # 先搜集主楼，主楼搜集完后标1

        while 1:
            for current in replies:
                temp_rdict = {
                    'rpid':current[0],
                    'root':current[1],
                    'nickname':current[2],
                    'uid':current[3],
                    'replytime':current[4],
                    'lastactivetime':current[5],
                    'content':current[6],
                    'replies':{}
                }

                if stat is False and current[1] is None:     # 正在搜集主楼并且是主楼
                    temp_dict['replies']['r'+str(current[0])] = temp_rdict
                
                elif stat is True and current[1] != None:     # 正在搜集楼中楼并且是楼中楼
                    for key in temp_dict['replies']:
                        if temp_dict['replies'][key]['rpid'] == current[1]:
                            temp_dict['replies'][key]['replies']['r'+str(current[0])] = temp_rdict
                            break

            if stat:
                break
            else:
                stat = True
        
        root['xml_content'][i['alias']] = temp_dict

    xml_str = xmltodict.unparse(root, pretty=1)

    with open('replies.xml', 'w+', encoding='UTF-8') as x:
        x.write(xml_str)


