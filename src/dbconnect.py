#!/usr/bin/env python
# coding:utf-8
"""
Author : Vitaliy Zubriichuk
Contact : v@zubr.kiev.ua
Time    : 16.11.2021 16:52
"""

from mysql.connector import connect
from configparser import ConfigParser


def read_db_config(filename='config.ini', section='mysql'):
    """ Read database configuration file and return a dictionary object
    :param filename: name of the configuration file
    :param section: section of database configuration
    :return: a dictionary of database parameters
    """
    # create parser and read ini configuration file
    parser = ConfigParser()
    parser.read(filename)

    # get section
    db = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            db[item[0]] = item[1]
    else:
        raise Exception(
            '{0} not found in the {1} file'.format(section, filename))
    return db

db_config = read_db_config()

class Connection(object):
    def __init__(self, config):
        self.connection = config

    def __enter__(self):
        self.db = connect(**self.connection)
        self.cursor = self.db.cursor()
        return self

    def __exit__(self, type, value, traceback):
        self.db.close()

    def load_users(self, sql):
        query = sql
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        return result

    def add_new_user(self, idtg, firstname, lastname):
        query = '''
            INSERT INTO mebelxl_embud.users (ID, FirstName, LastName) VALUES (%s, %s, %s)
        '''
        self.cursor.execute(query, (idtg, firstname, lastname))
        self.db.commit()
        return 1



if __name__ == '__main__':
    with Connection(db_config) as sql:
        a = sql.load_users('SELECT ID FROM mebelxl_embud.users')
        print(a)
