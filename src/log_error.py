# -*- coding: utf-8 -*-
"""
Created on Thu Aug 30 16:24:54 2018

@author: v.shkaberda
"""

from os import getcwd, path
import time

def writelog(e):
    """ Write error log into file log.txt.
    """
    fname = path.join(getcwd(), 'log.txt')
    now = time.localtime()

    with open(fname, 'a') as f:
        f.write('{} {}\n'.format(time.strftime("%d-%m-%Y %H:%M:%S", now), e))


if __name__ == '__main__':
    try:
        1 / 0
    except ZeroDivisionError as e:
        writelog(e)