#!/usr/bin/env python
# coding:utf-8
"""
Author : Vitaliy Zubriichuk
Contact : v@zubr.kiev.ua
Time    : 15.11.2021 19:29
"""

import telebot
import log_error as writelog
import dbconnect as db
from configparser import ConfigParser



def read_tg_config(filename='config.ini', section='telegram'):
    """ Read telegram configuration file and return a dictionary object
    :param filename: name of the configuration file
    :param section: section of database configuration
    :return: a dictionary of database parameters
    """
    # create parser and read ini configuration file
    parser = ConfigParser()
    parser.read(filename)

    # get section
    api = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            api[item[0]] = item[1]
    else:
        raise Exception(
            '{0} not found in the {1} file'.format(section, filename))
    return api

# get telegram token
bot = telebot.TeleBot(read_tg_config()['token'])

# get connection to db
config = db.read_db_config()

def get_users(users):
    """ return list ids of all telegram's users """
    ids = []
    n = len(users)
    count = 0
    while count < n:
        for i in users[count]:
            ids.append(i)
            count += 1
    return ids

with db.Connection(config) as conn:
    ids = conn.load_users('SELECT ID FROM mebelxl_embud.users')
    user_list = get_users(ids)


name = ''
surname = ''
user_tg_id = int
# user_list.append(707061731)
print(user_list)


@bot.message_handler(commands=['start'])
def start_message(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    if message.from_user.id not in user_list:
        keyboard.row('Регистрация')
        bot.send_message(message.from_user.id,
                         'Привет, для начала работы нажмите кнопку "Регистрация"',
                         reply_markup=keyboard)
    if message.from_user.id in user_list:
        bot.register_next_step_handler(message, main_menu)


def main_menu(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    keyboard.row('Привет', 'Пока')
    bot.send_message(message.from_user.id, 'Привет',
                     reply_markup=keyboard)

@bot.message_handler(content_types=['text'])
def send_text(message):
    if message.text.lower() == 'привет':
        bot.send_message(message.from_user.id, 'Ещё раз привет!')
    elif message.text.lower() == 'пока':
        bot.send_message(message.from_user.id, 'Пока!')
    elif message.text.lower() == 'регистрация':
        bot.send_message(message.from_user.id, 'Введите имя')
        bot.register_next_step_handler(message, get_name)
    elif message.text.lower() == 'ОК':
        bot.register_next_step_handler(message, main_menu)


def get_name(message):
    global user_tg_id
    user_tg_id = message.from_user.id
    global name
    name = message.text
    bot.send_message(message.from_user.id, 'Какая у тебя фамилия?')
    bot.register_next_step_handler(message, get_surname)

def get_surname(message):
    global surname
    surname = message.text


    with db.Connection(config) as conn:
        register = conn.add_new_user(user_tg_id, name, surname)
        if register == 1:
            bot.send_message(message.from_user.id, 'ОК')

    print(f'Вы зарегились и ваше имя {name} и фамилия {surname} и ваш id {message.from_user.id}:')


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
