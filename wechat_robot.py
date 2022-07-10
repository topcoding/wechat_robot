# -*- coding: utf-8 -*-

import itchat
import sqlite3
import os
import time
import requests
from apscheduler.schedulers.blocking import BlockingScheduler


PUNCH_TYPE_WORKOUT = 1
PUNCH_TYPE_SLEEP = 2

ai_chat_switch = True

AI_CHATROOM_WHITELIST = ['<替换成实际的群名>']


def save_db(punch_type, owner, timestamp = None):
    conn = sqlite3.connect('punch-card.db')
    cursor = conn.cursor()
    if timestamp is None:
        punch_time = (int) (time.time())
    else:
        punch_time = timestamp
    cursor.execute("insert into punch_card(punch_type, owner, updated_at) values(%d, '%s', %d)"
                   % (punch_type, owner, punch_time))
    conn.commit()
    conn.close()

@itchat.msg_register(itchat.content.TEXT)
def text_reply(msg):
    print(msg)
    timestamp = (int) (time.time())
    global ai_chat_switch
    if msg.text == '健身打卡':
        save_db(PUNCH_TYPE_WORKOUT, msg.User.NickName, timestamp)
        itchat.send('%s，您好，您于%s健身打卡成功' % (msg.User.NickName, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())), toUserName='filehelper')
    elif msg.text == '睡觉打卡':
        save_db(PUNCH_TYPE_SLEEP, msg.User.NickName, timestamp)
        itchat.send('%s，您好，您于%s睡觉打卡成功' % (msg.User.NickName, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())), toUserName='filehelper')
    elif msg.text == '拍照':
        img_file = '%d.jpg' % timestamp
        os.system('fswebcam %s' % img_file)
        itchat.send_image(img_file, toUserName='filehelper')
    elif msg.text == '看看家里':
        os.system('linphonecsh exit; linphonecsh init -V -c .linphonerc')
        time.sleep(1)
        os.system('linphonecsh generic "call <替换成实际的linphone账号，需注册>"')
    elif msg.text == '挂断视频':
        os.system('linphonecsh exit')
    elif msg.text == '群聊':
        ai_chat_switch = True
    elif msg.text == '群聊取消':
        ai_chat_switch = False
    else:
        # do nothing
        pass

@itchat.msg_register('Text', isGroupChat = True)
def group_reply(msg):
    if ai_chat_switch and msg['isAt'] and msg['User']['NickName'] in AI_CHATROOM_WHITELIST:
        print(msg)
        return u'@%s\u2005%s' % (msg['ActualNickName'], ai_chat(msg))

def ai_chat(msg):
    url = 'http://api.qingyunke.com/api.php?key=free&appid=0&msg=%s' % msg
    response = requests.get(url)
    return response.json()["content"].replace('{br}', '\n')

def weather_report():
    msg = ai_chat('上海天气')
    itchat.get_chatrooms(update=True)
    chatrooms = itchat.search_chatrooms(name='<替换成实际的群名>')
    chatroom = itchat.update_chatroom(chatrooms[0]['UserName'])
    itchat.send_msg(msg=msg,toUserName=chatroom['UserName'])


if __name__ == '__main__':
    itchat.auto_login(hotReload=True)
    itchat.run(blockThread=False)

    scheduler = BlockingScheduler()
    scheduler.add_job(weather_report, 'cron', day_of_week='*', hour=9, minute=0, second=0)
    scheduler.start()
