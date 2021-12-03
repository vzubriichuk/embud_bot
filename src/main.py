#!/usr/bin/env python
# coding:utf-8
"""
Author : Vitaliy Zubriichuk
Contact : v@zubr.kiev.ua
Time    : 15.11.2021 19:29
"""
from gc import get_objects

import ast
import telebot
import dbconnect as db
import log_error as writelog
from telebot import types
from dataclasses import dataclass
from configparser import ConfigParser
from shutil import copy, copy2
from pathlib import Path


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


@dataclass
class User:
    uid: int = None
    name: str = None
    surname: str = None
    object_id: int = None
    object_name: str = None
    list_files: list = None
    count_files: int = 0
    comment: str = None

user = User()
user.list_files = []

def convert_to_list(users):
    """ return list ids of all telegram's users from tuple to int """
    list = []
    n = len(users)
    count = 0
    while count < n:
        for i in users[count]:
            list.append(i)
            count += 1
    return list


with db.Connection(config) as conn:
    # получаем список пользователей сервиса
    ids = conn.load_users('SELECT ID FROM mebelxl_embud.users')
    user_list = convert_to_list(ids)
    # выгружаем список активных обьектов
    object_list = dict(conn.get_objects())

print(user_list)


icon_register = '👤'
icon_create = '🔥'
icon_check = 'ℹ'
icon_object = '🚧'
icon_home = '⤴'
icon_file_y = '✅'
icon_file_n = '❌'
icon_send_order = '🚀'


@bot.message_handler(commands=['start'])
def start_message(message):
    if message.from_user.id not in user_list:
        keyboard = types.ReplyKeyboardMarkup(row_width=1,
                                             resize_keyboard=True,
                                             one_time_keyboard=True)
        keyboard.row(icon_register + '  ' + 'Регистрация')
        bot.send_message(message.from_user.id,
                         'Привет, идентифицируйте себя, нажав кнопку "Регистрация"',
                         reply_markup=keyboard)
    else:
        menu_keyboard(message)


@bot.callback_query_handler(func=lambda query: 'begin_work' == query.data)
def menu_keyboard(message):
    menu_list = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    menu_list.row(icon_create + '  ' + 'Создать заявку')
    menu_list.row(icon_check + '  ' + 'Проверить статус заявки')
    bot.send_message(message.from_user.id,
                     'Начните с создания новой заявки', reply_markup=menu_list)


@bot.message_handler(content_types=['text'])
def send_text(message):
    data = message.text
    if data.startswith(icon_register):
        bot.send_message(message.from_user.id, 'Введите имя')
        bot.register_next_step_handler(message, get_name)
    elif data.startswith(icon_create):
        markup = types.ReplyKeyboardMarkup(row_width=1)
        for key, value in object_list.items():
            markup.row(icon_object + '  ' + value)
        markup.row(icon_home + '  ' + 'Главное меню')
        bot.send_message(message.from_user.id, "Выберите объект из списка ",
                         reply_markup=markup)
    elif data.startswith(icon_object):
        user.object_name = data
        post_comment(message)
    elif data.startswith(icon_file_y) and user.count_files == 0:
        menu = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        menu.row(icon_home + '  ' + 'Главное меню')
        bot.send_message(message.from_user.id, "Прикрепите 1 файл", reply_markup=menu)
        bot.register_next_step_handler(message, get_file)
    elif data.startswith(icon_file_y) and user.count_files > 0:
        menu = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        menu.row(icon_home + '  ' + 'Главное меню')
        bot.send_message(message.from_user.id, "Прикрепите еще 1 файл", reply_markup=menu)
        bot.register_next_step_handler(message, get_file)
    elif data.startswith(icon_file_n):
        final_menu = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        final_menu.row(icon_send_order + '  ' + 'Отправить заявку')
        final_menu.row(icon_home + '  ' + 'Главное меню')
        if user.count_files > 0:
            bot.send_message(message.from_user.id, "Файл(-ы) прикреплены.  " 
                                                   "Подтвердите отправку заявки.",
                             reply_markup=final_menu)
        else:
            bot.send_message(message.from_user.id, "Подтвердите отправку заявки.",
                             reply_markup=final_menu)

        bot.register_next_step_handler(message, approve_order)
    elif data.startswith(icon_check):
        bot.send_message(message.from_user.id, "Данная функция в разработке.")
    elif data.startswith(icon_home):
        menu_keyboard(message)



"""
Functions step-by-step
"""

def get_name(message):
    user.uid = message.from_user.id
    user.name = message.text
    bot.send_message(message.from_user.id, 'Ваша фамилия?')
    bot.register_next_step_handler(message, get_surname)

def get_surname(message):
    user.surname = message.text

    with db.Connection(config) as sql:
        register = sql.add_new_user(user.uid, user.name, user.surname)
        if register == 1:
            bot.send_message(message.chat.id, '',
                             reply_markup=menu_keyboard(message))

def post_comment(message):
    menu = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    menu.row(icon_home + '  ' + 'Главное меню')
    bot.send_message(message.from_user.id, 'Напишите список необходимых материалов одним сообщением', reply_markup=menu)
    bot.register_next_step_handler(message, get_comment)

def get_comment(message):
    user.comment = message.text
    menu_file_yn = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    menu_file_yn.row(icon_file_y + '  ' + 'Да', icon_file_n + '  ' + 'Нет')
    menu_file_yn.row(icon_home + '  ' + 'Главное меню')
    bot.send_message(message.chat.id, 'Хотите ли вы добавить файл к заявке?', reply_markup=menu_file_yn)


from ftplib import FTP
import os
import io







def get_file(message):
    if message.content_type == 'document':
        download_document(message)
    elif message.content_type == 'photo':
        bot.send_message(message.chat.id,
                         'Отправлять можно файлы документов.'
                         ' Функция отправки фото в разработке.',)


def download_document(message):
    ftp = FTP()
    # ftp.set_debuglevel(2)
    ftp.connect('mebelxl.ftp.tools', 21)
    ftp.login('mebelxl_ftp', 'Embudbot1')
    ftp.dir()

    filename = message.document.file_name
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    bio = io.BytesIO(downloaded_file)
    ftp.storbinary(f'STOR {filename}', bio)
    add_more_files(filename)

def download_photo(message):
    photo_info = bot.get_file(message.photo[-1].file_id)
    print(photo_info.file_id)
    # bot.send_photo(message.chat.id, photo_info.file_id)
    src = 'C:/Dell/' + photo_info.file_path
    with open(src, 'wb') as new_file:
        # записываем данные в файл
        new_file.write(photo_info.file_id)

def add_more_files(filename):
    user.list_files.append(filename)
    user.count_files += 1
    menu_file_yn = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    menu_file_yn.row(icon_file_y + '  ' + 'Да', icon_file_n + '  ' + 'Нет')
    menu_file_yn.row(icon_home + '  ' + 'Главное меню')


def approve_order(message):
    bot.send_message(message.from_user.id, 'Заявка отправлена')
    # all right, go to main keyboard menu
    menu_keyboard(message)









@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    data = call.data
    if data == 'file_yes':
        valueFromCallBack = ast.literal_eval(call.data)[1]
        keyFromCallBack = ast.literal_eval(call.data)[2]
        user.object_id = keyFromCallBack
        bot.edit_message_text(chat_id=call.message.chat.id,
                              text=f'Вы выбрали объект: {valueFromCallBack}',
                              message_id=call.message.message_id,
                              reply_markup=post_comment(call),
                              # reply_markup=makeKeyboard(valueFromCallBack,
                              #                           keyFromCallBack),
                              parse_mode='HTML')

def makeKeyboard(value, id):
    user.object_id = id
    print(f'ID объекта: {user.object_id}')



    #
# @bot.message_handler(content_types=['text'])
# def send_text(message):
#     if message.text.lower() == 'создать заявку':
#         markup = telebot.types.InlineKeyboardMarkup(row_width=1)
#         button = telebot.types.InlineKeyboardButton(text='Выберите объект',
#                                                     callback_data='check')
#         markup.add(button)
#         print(1)
#         bot.send_message(message.chat.id, "Все доступные товары: ", reply_markup=markup)


# @bot.message_handler(func=lambda message: message.text.lower() == "Создайте")
# def cart(message):
#     bot.send_message(message.chat.id, "Все доступные товары: ", reply_markup=keyboard1)
#


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
