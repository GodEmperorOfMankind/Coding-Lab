from time import sleep
from telegram.ext import *
import telebot
from telebot import *
from dict import Dictionary
from datetime import date
from threading import Thread
from datetime import datetime

import sqlite3


API_KEY = '5238220008:AAFa2hOoMxEu-_xPpIte6iDWEo1MxQ4FIrA'
bot = telebot.TeleBot(API_KEY)
# Set up the logging

conn = sqlite3.connect('db/database.db', check_same_thread=False)
cursor = conn.cursor()


def db_table_val(user_id: int, user_name: str, username: str):
    try:
        cursor.execute('INSERT INTO Users (id, user_name,  user_tag) VALUES (?, ?, ?)',
                       (user_id, user_name, username))
        conn.commit()
        cursor.execute('INSERT INTO UserDay (user_id, days) VALUES (?, ?)',
                (user_id, 0))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, Dictionary.HELLO, reply_markup=get_buttons(message))


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if (message.text == Dictionary.BUTTON_REGISTER):
        register(message)
    if (message.text == Dictionary.BUTTON_ADD_TASK):
        add_task(message)
    if (message.text == Dictionary.BUTTON_HELP):
        help(message)
    if (message.text == Dictionary.BUTTON_CREATOR):
        creators(message)
    if (message.text == Dictionary.BUTTON_PAYMENTS):
        payments(message)
    if (message.text == Dictionary.BUTTON_SHOW_TASKS):
        show_tasks(message)
    if (message.text == Dictionary.BUTTON_YES or message.text == Dictionary.BUTTON_TASK_ALL_COMPLETED):
        completed_tasks(message)
    if (message.text == Dictionary.BUTTON_NO):
        not_completed_tasks(message)



def not_completed_tasks(message):
    try:
        if (not isRegistered(message)):
            raise sqlite3.IntegrityError
        us_id = message.from_user.id


        cursor.execute('SELECT days FROM UserDay WHERE user_id=?', (us_id,))
        row = cursor.fetchone()
        cursor.execute('UPDATE UserDay SET days = ? WHERE user_id=?', (int(row[0]) - 1, us_id))
        conn.commit()
        bot.send_message(message.chat.id, Dictionary.TASK_THANK, reply_markup=get_buttons(message))

        if (int(row[0]) - 1 <= -3):
            bot.send_message(message.chat.id, Dictionary.MESSAGE_PROBLEM, reply_markup=get_buttons(message))

    except sqlite3.IntegrityError:
        bot.send_message(
            message.chat.id, Dictionary.REGISTER_ERROR, reply_markup=get_buttons(message))
    except Exception as e:
        bot.send_message(message.chat.id, Dictionary.TASK_FAILED,
                         reply_markup=get_buttons(message)) 

def completed_tasks(message):

    try:
        if (not isRegistered(message)):
            raise sqlite3.IntegrityError
        us_id = message.from_user.id
        cursor.execute('SELECT id, isCompleted FROM Tasks WHERE user_id=? and date=? and isCompleted = 0',(us_id, date.today()))
        rows = cursor.fetchall()

        if (rows == None or len(rows) == 0):
            bot.send_message(message.chat.id, Dictionary.TASK_SHOW_NULL, reply_markup=get_buttons(message))
        else:
            for i in range(0, len(rows)):
                cursor.execute('UPDATE Tasks SET isCompleted = 1 WHERE id=?', (rows[i][0],))
                conn.commit()
            cursor.execute('SELECT days FROM UserDay WHERE user_id=?', (us_id,))
            row = cursor.fetchone()
            cursor.execute('UPDATE UserDay SET days = ? WHERE user_id=?', (int(row[0]) + 1, us_id))
            conn.commit()
            bot.send_message(message.chat.id, Dictionary.TASK_THANK, reply_markup=get_buttons(message))

    except sqlite3.IntegrityError:
        bot.send_message(
            message.chat.id, Dictionary.REGISTER_ERROR, reply_markup=get_buttons(message))
    except Exception as e:
        bot.send_message(message.chat.id, Dictionary.TASK_FAILED,
                         reply_markup=get_buttons(message)) 

def show_tasks(message):

    try:
        if (not isRegistered(message)):
            raise sqlite3.IntegrityError
        us_id = message.from_user.id
        cursor.execute('SELECT task FROM Tasks WHERE user_id=? and date=? and isCompleted = 0',(us_id, date.today()))
        rows = cursor.fetchall()

        if (rows == None or len(rows) == 0):
            bot.send_message(message.chat.id, Dictionary.TASK_SHOW_NULL, reply_markup=get_buttons(message))
        else:
            tasks_list = Dictionary.TASK_SHOW_INFO + '\n'

            for i in range(0, len(rows)):
                tasks_list += str(i + 1) + ") " + rows[i][0] + '\n'
            bot.send_message(message.chat.id, tasks_list,reply_markup=get_buttons(message))

    except sqlite3.IntegrityError:
        bot.send_message(
            message.chat.id, Dictionary.REGISTER_ERROR, reply_markup=get_buttons(message))
    except Exception:
        bot.send_message(message.chat.id, Dictionary.TASK_FAILED,
                         reply_markup=get_buttons(message))   
def payments(message):
    bot.send_message(message.chat.id, Dictionary.PAYMENTS)    
def creators(message):
    bot.send_message(message.chat.id, Dictionary.CREATOR)
def help(message):
    bot.send_message(message.chat.id, Dictionary.HELP)
def register(message):
    us_id = message.from_user.id
    us_name = message.from_user.first_name
    username = message.from_user.username

    message_for_user = ""

    if db_table_val(user_id=us_id, user_name=us_name, username=username):
        message_for_user = Dictionary.REGISTER_SUCC
    else:
        message_for_user = Dictionary.REGISTER_ALREADY

    bot.send_message(message.chat.id, message_for_user)

    message_for_user = Dictionary.AFTER_REGISTER_SUCC

    bot.send_message(message.chat.id, message_for_user, reply_markup=get_buttons(message))

def isRegistered(message):
    try:
        us_id = message.from_user.id
        cursor.execute("SELECT id FROM Users WHERE id = ?", (us_id, ))
        rows = cursor.fetchone()
        if (rows == None):
            return False
        return True
    except Exception:
        return False

def add_task(message):
    try:
        if (not isRegistered(message)):
            raise sqlite3.IntegrityError
        msg = bot.send_message(message.chat.id, Dictionary.TASK_ENTER_NAME, reply_markup = types.ReplyKeyboardRemove(selective=True))
        bot.register_next_step_handler(msg, enter_task)
    except sqlite3.IntegrityError:
        bot.send_message(
            message.chat.id, Dictionary.REGISTER_ERROR, reply_markup = get_buttons(message))
def enter_task(message):
    try:
        us_id = message.from_user.id
        cursor.execute('PRAGMA foreign_keys = ON;')
        conn.commit()
        cursor.execute('INSERT INTO Tasks (user_id, task, date, isCompleted) VALUES (?, ?, ?, ?)',
                       (us_id, message.text, date.today(), 0))
        conn.commit()
        bot.send_message(message.chat.id, Dictionary.TASK_ADDED,
                         reply_markup=get_buttons(message))
    except Exception:
        bot.send_message(message.chat.id, Dictionary.TASK_FAILED,
                         reply_markup=get_buttons(message))

def get_buttons(message):
    

    markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True)

    button_help = types.KeyboardButton(Dictionary.BUTTON_HELP)
    button_creators = types.KeyboardButton(Dictionary.BUTTON_CREATOR)
    button_payments = types.KeyboardButton(Dictionary.BUTTON_PAYMENTS)
    
    if (not isRegistered(message)):
        button_register = types.KeyboardButton(Dictionary.BUTTON_REGISTER)
        markup_reply.add(button_register, button_help, button_creators, button_payments)
    else:
        button_add_task = types.KeyboardButton(Dictionary.BUTTON_ADD_TASK)
        button_show_tasks = types.KeyboardButton(Dictionary.BUTTON_SHOW_TASKS)
        button_completed_all_tasks = types.KeyboardButton(Dictionary.BUTTON_TASK_ALL_COMPLETED)
        markup_reply.add(button_add_task, button_show_tasks, button_help, button_creators, button_payments, button_completed_all_tasks)

    return markup_reply


def notifyEndDay():
    try:
        while True:
            now = datetime.now()
            if (now.strftime("%H:%M") == "22:58"):
                cursor.execute("SELECT id FROM Users")
                rows = cursor.fetchall()
                for i in range(0, len(rows)):
                    user_id = rows[i][0]
                    cursor.execute('SELECT task FROM Tasks WHERE user_id=? and date=? and isCompleted = 0',(user_id, date.today()))
                    rows = cursor.fetchall()
                    if (len(rows) > 0):
                        markup_reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
                        button_yes = types.KeyboardButton(Dictionary.BUTTON_YES)
                        button_no = types.KeyboardButton(Dictionary.BUTTON_NO)
                        markup_reply.add(button_yes, button_no)
                        bot.send_message(user_id, text="Have you completed your tasks for today?", reply_markup = markup_reply)
                sleep(60)
    except Exception:
        pass


th = Thread(target=notifyEndDay, args=())
th.start()
bot.polling(none_stop=True)

