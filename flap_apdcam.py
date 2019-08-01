# -*- coding: utf-8 -*-
"""
Created on Sat Dec  8 23:23:49 2018

@author: Zoletnik

This is the flap module for APDCAM
"""

import os.path
import flap
from decimal import *
import numpy as np
import copy
import os
import fnmatch

if (flap.VERBOSE):
    print("Importing flap_apdcam")


def apdcam_get_config(xml):
    retval = {}
    try:
        camera_family = xml.head.attrib['Device']
    except KeyError:
        raise TypeError("Device type is not found in XML file head.")
    retval['camera_family'] = camera_family
    try:
        ADCMult= Decimal(xml.get_element('ADCSettings', 'ADCMult')['Value'])
        ADCDiv= Decimal(xml.get_element('ADCSettings','ADCDiv')['Value'])
        retval['f_ADC'] = Decimal(20e6)*ADCMult/ADCDiv
        samplediv= Decimal(xml.get_element('ADCSettings','Samplediv')['Value'])
        retval['f_sample'] = retval['f_ADC'] / samplediv
        retval['sampletime'] = Decimal(1.)/retval['f_sample']
        retval['samplenumber'] = int(xml.get_element('ADCSettings', 'SampleNumber')['Value'])
        retval['bits'] = int(xml.get_element('ADCSettings', 'Bits')['Value'])
        trigger = Decimal(xml.get_element('ADCSettings', 'Trigger')['Value'])
        if (trigger < 0):
            trigger = float(0)
        retval['starttime'] = trigger
        if (camera_family == 'APDCAM-10G'):
            mask1 = int(xml.get_element('ADCSettings', 'ChannelMask1')['Value'],16)
            mask2 = int(xml.get_element('ADCSettings', 'ChannelMask2')['Value'],16)
            mask3 = int(xml.get_element('ADCSettings', 'ChannelMask3')['Value'],16)
            mask4 = int(xml.get_element('ADCSettings', 'ChannelMask4')['Value'],16)
            chmask = mask1 + (mask2<<32) + (mask3<<64) + (mask4<<96)
        if (camera_family == 'APDCAM'):
            chmask = int(xml.get_element('ADCSettings','ChannelMask')['Value'],16)
    except ValueError as e:
        raise e
    retval['chmask'] = chmask
    return retval


def apdcam_get_data(exp_id=None, data_name=None, no_data=False, options=None, coordinates=None, data_source=None):
    """ Data read function for APDCAM 1G and 10G.
    data_name: ADCxxx (string): ADC number. Unix style regular expressions are allowed:
                       ADC*
                       ADC[2-5]
                       Can also be a list of data names, eg. ['ADC1','ADC3']
    coordinates: List of flap.Coordinate() or a single flap.Coordinate
                 Defines read ranges. The following coordinates are interpreted:
                     'Sample': The read samples
                     'Time': The read times
                     Only a single equidistant range is interpreted.
    options:
        'Scaling':  'Digit'
                    'Volt'
        'Datapath': Data path (string)
    """

    default_options = {'Datapath':'data',
                       'Scaling':'Digit'
                       }
    if (data_source is None):
        data_source = 'APDCAM'
    _options = flap.config.merge_options(default_options,options,data_source=data_source)
    datapath = _options['Datapath']

    xmlfile = os.path.join(datapath,'APDCAM_config.xml')
    xml = flap.FlapXml()
    try:
        xml.read_file(xmlfile)
    except Exception:
        raise IOError("Error reading XML file:" + xmlfile)
    if (xml.head.tag != 'General'):
        raise TypeError("XML file " + xmlfile + " is not an APDCAM xml file.")
    try:
        camera_family = xml.head.attrib['Device']
    except KeyError:
        raise TypeError("Device type is not found in XML file head.")
    t = apdcam_get_config(xml)
    fnames = os.listdir(datapath)
    chlist = []
    chlist_adc = []
    if (camera_family == 'APDCAM-10G'):
        fnames = fnmatch.filter(fnames, "Channel_[0-9][0-9][0-9].dat")
        for fn in fnames:
            chlist.append(int(fn[8:11]) + 1)
            chlist_adc.append('ADC' + str(int(fn[8:11]) + 1))
    else:
        fnames = fnmatch.filter(fnames, "Channel[0-9][0-9].dat")
        for fn in fnames:
            chlist.append(int(fn[7:9]) + 1)
            chlist_adc.append('ADC' + str(int(fn[7:9]) + 1))
    if type(data_name) is not list:
        chspec = [data_name]
    else:
        chspec = data_name

    try:
        chlist_proc, ch_index = flap.select_signals(chlist_adc,chspec)
    except ValueError as e:
        raise e
    ch_proc = [chlist[chi] for chi in ch_index]

    read_range = None
    read_samplerange = None
    if (coordinates is not None):
        if (type(coordinates) is not list):
             _coordinates = [coordinates]
        else:
            _coordinates = coordinates
        for coord in _coordinates:
            if (type(coord) is not flap.Coordinate):
                raise TypeError("Coordinate description should be flap.Coordinate.")
            if (coord.unit.name is 'Time'):
                if (coord.mode.equidistant):
                    read_range = [float(coord.c_range[0]),float(coord.c_range[1])]
                else:
                    raise NotImplementedError("Non-equidistant Time axis is not implemented yet.")
                break
            if coord.unit.name is 'Sample':
                if (coord.mode.equidistant):
                    read_samplerange = coord.c_range
                else:
                    raise \
                        NotImplementedError("Non-equidistant Sample axis is not implemented yet.")
                break
    if ((read_range is None) and (read_samplerange is None)):
        read_samplerange = np.array([0,t['samplenumber']])
    if (read_range is not None):
        read_range = np.array(read_range)
    if (read_samplerange is None):
        read_samplerange = np.rint((read_range - float(t['starttime'])) / float(t['sampletime']))
    else:
        read_samplerange = np.array(read_samplerange)
    if ((read_samplerange[1] < 0) or (read_samplerange[0] >= t['samplenumber'])):
        raise ValueError("No data in time range.")
    if (read_samplerange[0] < 0):
        read_samplerange[0] = 0
    if (read_samplerange[1] >= t['samplenumber']):
        read_samplerange[1] = t['samplenumber']
    ndata = int(read_samplerange[1] - read_samplerange[0] + 1)
    if (_options['Scaling'] is 'Volt'):
        scale_to_volts = True
        dtype = float
        data_unit = flap.Unit(name='Signal',unit='Volt')
    else:
        scale_to_volts = False
        dtype = np.int16
        data_unit = flap.Unit(name='Signal',unit='Digit')

    if (no_data is False):
        if (len(ch_proc) is not 1):
            data_arr = np.empty((ndata,len(ch_proc)),dtype=dtype)
        for i in range(len(ch_proc)):
            fn = os.path.join(datapath,fnames[ch_index[i]])
            try:
                f = open(fn,"rb")
            except OSError:
                raise OSError("Error opening file: " + fn)
            try:
                f.seek(int(read_samplerange[0]),os.SEEK_SET)
                if (len(ch_proc) is 1):
                    data_arr = np.fromfile(f,dtype=np.int16,count=ndata)
                else:
                    d = np.fromfile(f,dtype=np.int16,count=ndata)
                    data_arr[:,i] = d
            except Exception:
                raise IOError("Error reading from file: " + fn)
        if (scale_to_volts):
            if (camera_family == 'APDCAM-10G'):
                data_arr = ((2 ** t['bits'] - 1) - data_arr) / (2. ** t['bits'] - 1) * 2
            else:
                data_arr = data_arr / (2.**t['bits'] - 1) * 2
        else:
            if (camera_family == 'APDCAM-10G'):
                data_arr = (2**t['bits'] - 1) - data_arr
            f.close

    coord = [None]*data_arr.ndim * 2
    c_mode = flap.CoordinateMode(equidistant=True)
    coord[0] = copy.deepcopy(flap.Coordinate(name='Sample',unit='n.a.',
                                             mode=c_mode,
                                             shape=ndata,
                                             start=read_samplerange[0],
                                             step=1,
                                             dimension_list=[0]))
    if (read_range is None):
        read_range = float(t['starttime']) + read_samplerange * float(t['sampletime'])
    coord[1] = copy.deepcopy(flap.Coordinate(name='Time',unit='Second',
                                             mode=c_mode,
                                             shape=ndata,
                                             start=read_range[0],
                                             step=t['sampletime'],
                                             dimension_list=[0])
                             )
    if (data_arr.ndim > 1):
        c_mode = flap.CoordinateMode(equidistant=False)
        coord[2] = copy.deepcopy(flap.Coordinate(name='Channel',
                                                 unit='n.a.',
                                                 mode=c_mode,
                                                 shape=len(ch_proc),
                                                 values=ch_proc,
                                                 dimension_list=[1])
                                 )
        coord[3] = copy.deepcopy(flap.Coordinate(name='Signal name',
                                                 unit='n.a.',
                                                 mode=c_mode,
                                                 shape=len(ch_proc),
                                                 values=chlist_proc,
                                                 dimension_list=[1])
                                 )

    data_title = camera_family + " data"
    if (data_arr.ndim == 1):
        data_title += " " + chlist_proc[0]
    d = flap.DataObject(data_array=data_arr,data_unit=data_unit,
                        coordinates=coord, exp_id=None,data_title=data_title)
    return d


def add_coordinate(data_object, new_coordinates, options=None):
    raise NotImplementedError("Coordinate conversions not implemented yet.")

def register(data_source=None):
    if (data_source is None):
        data_source = 'APDCAM'
    flap.register_data_source(data_source, get_data_func=apdcam_get_data, add_coord_func=add_coordinate)
