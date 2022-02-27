# -*- coding: utf-8 -*-
"""
Created on Thu Jul 26 18:33:13 2018

@author: Zoletnik
"""

import configparser

def get(file,section,key) :
    """ Reads an element from a configuration file
    The file format is 
    [Section]
    key = value
    # comment
    """
    config = configparser.ConfigParser()
    try:
        config.read(file)
    except :
        err = "Error reading file "+file
        return err, None
    try:
        value = config[section][key]
    except:
        err = "Error reading key "+key+" from section "+section+" from file "+file
        return err,None
    return "", value
    