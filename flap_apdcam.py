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
            retval['Bias 1'] = float(xml.get_element('APDCAM', 'DetectorBias1')['Value'])
            retval['Bias 2'] = float(xml.get_element('APDCAM', 'DetectorBias2')['Value'])   
            retval['Detector temp 1'] = float(xml.get_element('APDCAM', 'DetectorTemp1')['Value'])
            retval['Detector temp 2'] = float(xml.get_element('APDCAM', 'DetectorTemp2')['Value'])
        if (camera_family == 'APDCAM'):
            chmask = int(xml.get_element('ADCSettings','ChannelMask')['Value'],16)
    except ValueError as e:
        raise e
    # These are optional
    try:
       retval['Camera type'] = xml.get_element('APDCAM', 'CameraType')['Value']
    except ValueError:
        pass
    try:
       retval['Camera version'] = int(xml.get_element('APDCAM', 'CameraVersion')['Value']) 
    except ValueError:
        pass
    retval['chmask'] = chmask
    try:
        retval['Sensor angle'] = int(xml.get_element('APDCAM', 'CameraType')['Value'])      
    except ValueError:
        pass
         
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
    return retval

def apdcam_types_versions():
    """
    Returns the possible camera types and versions. 
    

    Returns
    -------
    camera_types: list of strings
        The list of possible camera types
    camera_version: list of lists
        For each camera type lists the possible version numbers
    """
    
    camera_types = [#APDCAM-10G:
                    'APDCAM-10G_4x32',   # 4x32 pixel
                    'APDCAM-10G_8x8',    # 8x8 pixel
                    'APDCAM-10G_4x16',   # 4x16 pixel, subarray of 4x32
                    'APDCAM-10G_8x16',   # 8x16 pixel, 8 pixel in one S8550 array
                    'APDCAM-10G_8x16A',  # 8x16 pixel, 8 pixxels in two S8550 arrays
                    #APDCAM-1G: 
                    'APDCAM-1G',         # Standard APDCAM-1G (Horizontal array)
                    'APDCAM-1G_90',      #APDCAM-1G with sensor rotated 90 degree CCW
                    'APDCAM-1G_180',     #APDCAM-1G with sensor rotated 180 degree CCW
                    'APDCAM-1G_270'      # APDCAM-1G with sensor rotated 270 degree CCW
                    ]
    camera_versions = [#APDCAM-10G:
                        [1,0,2],   # 4x32 pixel
                        [1,0,2],   # 8x8 pixel
                        [1,0,2],   # 4x16 pixel, subarray of 4x32
                        [1,0,2],   # 8x16 pixel, 8 pixel in one S8550 array
                        [1]    ,   # 8x16 pixel, 8 pixxels in two S8550 arrays
                        #APDCAM-1G: 
                        [],        # Standard APDCAM-1G (Horizontal array)
                        [],        #APDCAM-1G with sensor rotated 90 degree CCW
                        [],        #APDCAM-1G with sensor rotated 180 degree CCW
                        []         # APDCAM-1G with sensor rotated 270 degree CCW
                      ]   
    return camera_types, camera_versions
    

def apdcam_get_data(exp_id=None, data_name=None, no_data=False, options=None, coordinates=None, data_source=None,
                    ):
    """ 
    Data read function for APDCAM 1G and 10G.
    
    Parameters
    ----------
    data_name: string
               ADCxxx: ADC number. Unix style regular expressions are allowed:
                       ADC*
                       ADC[2-5]
                       Can also be a list of data names, eg. ['ADC1','ADC3']
               APD-r-c (string): APD pixel number
    coordinates: List of flap.Coordinate() or a single flap.Coordinate
                 Defines read ranges. The following coordinates are interpreted:
                     'Sample': The read samples
                     'Time': The read times
                     Only a single equidistant range is interpreted.
    options: dict
        'Scaling':  'Digit'
                    'Volt'
        'Datapath': Data path (string)
        'Camera type': string
                        None: Determine camera type from xml file
                        string: Set camera type as below.
                        The camera type:
                         APDCAM-10G:
                             APDCAM-10G_4x32
                             APDCAM-10G_8x8
                             APDCAM-10G_4x16
                             APDCAM-10G_8x16
                             APDCAM-10G_8x16A
                         APDCAM-1G: 
                             APDCAM-1G : Standard APDCAM-1G (Horizontal array)
                             APDCAM-1G_90: APDCAM-1G with sensor rotated 90 degree CCW
                             APDCAM-1G_180: APDCAM-1G with sensor rotated 180 degree CCW
                             APDCAM-1G_270: APDCAM-1G with sensor rotated 270 degree CCW
        'Camera_version': int
            Only applicable to 10G cameras: 0,1,2
   
    Return value
    ------------
    flap.DataObject:
        The output flap data object. The data dimension depends on the requested channels.
        If only 1 channel is requested: 1D
        If any of the channels is ADCxxx or the camera is FC type or the requested channels
        do not form a 2D array: 2D
        If the camera is 2D and the requested channels form a regular 2D subarray of it: 3D
            
    """

    default_options = {'Datapath':'data',
                       'Scaling':'Digit',
                       'Camera type': None,
                       'Camera version': None
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
        raise TypeError("APDCAM family is not found in XML file head.")
    t = apdcam_get_config(xml)
    fnames = os.listdir(datapath)
    if (camera_family == 'APDCAM-10G'):
        from .apdcam_control.apdcam10g_channel_map import apdcam10g_channel_map
        camera_type = _options['Camera type']
        if (camera_type is None): 
            try:
                camera_type = t['Camera type']
            except KeyError:
                raise ValueError("The camera type was neither found in the xml file nor was it given as an option.")
        if (camera_type[:11].lower() != 'apdcam-10g_' ):
            raise ValueError("Invalid camera type '{:s}'.".format(camera_type))
        camera_version = _options['Camera version']
        if (camera_version is None):
            try:
                camera_version = t['Camera version']
            except KeyError:
                camera_version = 1
        chmap = apdcam10g_channel_map(camera_type=camera_type[11:],camera_version=camera_version)
    elif (camera_family == 'APDCAM'):
        from .apdcam_control.apdcam_channel_map import apdcam_channel_map
        if (_options['Camera type'] is not None): 
            camera_type = _options['Camera type']
            if (camera_type == 'APDCAM-1G'):
                sensor_angle = 0
            else:
                sensor_angle = int(camera_type[9:])
        else:
            try:
                sensor_angle = t['Sensor angle']
            except KeyError:
                sensor_angle = 0
        chmap = apdcam_channel_map(sensor_rotation=sensor_angle) 
    else:
        raise ValueError("Unknown camera family in xml file: {:s}".camera_family)
    
    # Settting up a list of possible channel names and associated file names
    ch_names = []
    fnames = []
    col_list = []
    row_list = []
    adc_list = []
    if (chmap.ndim == 2):
        nrow = chmap.shape[0]
        ncol = chmap.shape[1]
        for ir in range(nrow):
            for ic in range(ncol):
                ch_names.append('APD-{:d}-{:d}'.format(ir + 1,ic + 1))
                row_list.append(ir + 1)
                col_list.append(ic + 1)
                ch_names.append('ADC{:d}'.format(chmap[ir,ic]))
                row_list.append(None)
                col_list.append(None)
                if (camera_family == 'APDCAM-10G'):
                    fn = 'Channel_{:03d}.dat'.format(chmap[ir,ic] - 1)
                else:
                    fn = 'Channel{:02d}.dat'.format(chmap[ir,ic] - 1)
                fnames.append(fn)
                fnames.append(fn)
                adc_list.append(chmap[ir,ic])
                adc_list.append(chmap[ir,ic])
    else:
        for ir in range(nrow):
                ch_names.append('APD-{:d}'.format(ir + 1))
                ch_names.append('ADC{:d}'.format(chmap[ir]))
                if (camera_family == 'APDCAM-10G'):
                    fn = 'Channel_{:03d}.dat'.format(chmap[ir] - 1)
                else:
                    fn = 'Channel{:02d}.dat'.format(chmap[ir] - 1)
                fnames.append(fn)
                fnames.append(fn)
                adc_list.append(chmap[ir,ic])
                adc_list.append(chmap[ir,ic])
        
    if type(data_name) is not list:
        chspec = [data_name]
    else:
        chspec = data_name

    # Selecting the required channels
    try:
        chname_proc, ch_index = flap.select_signals(ch_names,chspec)
    except ValueError as e:
        raise e
        
    
    fnames_proc = [fnames[i] for i in ch_index]
    col_proc = [col_list[i] for i in ch_index]
    row_proc = [row_list[i] for i in ch_index]
    adc_proc = [adc_list[i] for i in ch_index]
    
    # Determining the dimension of the output data array
    if (len(chname_proc) == 1):
        outdim = 1
    elif (chmap.ndim == 1):
        outdim = 2
    else:
        outdim = 3
        # If any of the channels has None in column or row, the output is 2D
        for c,r in zip(col_proc,row_proc):
            if ((c is None) or (r is None)):
                outdim = 2
                break
        if (outdim == 3):
            out_row_list = sorted(set(row_proc))
            out_col_list = sorted(set(col_proc))
            if (len(out_col_list) * len(out_row_list) != len(chname_proc)):
                outdim = 2
            else:
                out_col_index = []
                out_row_index = []
                for i in range(len(row_proc)):
                    out_row_index.append(out_row_list.index(row_proc[i]))
                    out_col_index.append(out_col_list.index(col_proc[i]))
                    
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
            if (coord.unit.name == 'Time'):
                if (coord.mode.equidistant):
                    if (coord.c_range is None):
                        continue
                    read_range = [float(coord.c_range[0]),float(coord.c_range[1])]
                else:
                    raise NotImplementedError("Non-equidistant Time axis is not implemented yet.")
                break
            if coord.unit.name == 'Sample':
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
        read_samplerange[1] = t['samplenumber'] - 1
    ndata = int(read_samplerange[1] - read_samplerange[0] + 1)
    if (_options['Scaling'] == 'Volt'):
        scale_to_volts = True
        dtype = float
        data_unit = flap.Unit(name='Signal',unit='Volt')
    else:
        scale_to_volts = False
        dtype = np.int16
        data_unit = flap.Unit(name='Signal',unit='Digit')
    
    if (outdim == 1):
        data_arr = np.empty(ndata,dtype=dtype) 
    elif (outdim == 2):
        data_arr = np.empty((ndata,len(chname_proc)),dtype=dtype)
    else:
        data_arr = np.empty((ndata,len(out_row_list),len(out_col_list)),dtype=dtype)
    
    if (no_data is False):
        for i in range(len(chname_proc)):
            fn = os.path.join(datapath,fnames_proc[i])
            try:
                f = open(fn,"rb")
            except OSError:
                raise OSError("Error opening file: " + fn)
            try:
                f.seek(int(read_samplerange[0]),os.SEEK_SET)
                d = np.fromfile(f,dtype=np.int16,count=ndata)
            except IOError:
                raise IOError("Error reading from file: " + fn)
            f.close()
            if (outdim == 1):
                data_arr = d
            elif (outdim == 2):
                data_arr[:,i] = d
            else:
                data_arr[:,out_row_index[i],out_col_index[i]] = d
                
        if (scale_to_volts):
            if (camera_family == 'APDCAM-10G'):
                data_arr = ((2 ** t['bits'] - 1) - data_arr) / (2. ** t['bits'] - 1) * 2
            else:
                data_arr = data_arr / (2.**t['bits'] - 1) * 2
        else:
            if (camera_family == 'APDCAM-10G'):
                data_arr = (2**t['bits'] - 1) - data_arr

    coord = []
    c_mode = flap.CoordinateMode(equidistant=True)
    coord.append(flap.Coordinate(name='Sample',
                                 unit='n.a.',
                                 mode=c_mode,
                                 shape=ndata,
                                 start=read_samplerange[0],
                                 step=1,
                                 dimension_list=[0]
                                 )
                 )
    if (read_range is None):
        read_range = float(t['starttime']) + read_samplerange * float(t['sampletime'])
    coord.append(flap.Coordinate(name='Time',
                                 unit='Second',
                                 mode=c_mode,
                                 shape=ndata,
                                 start=read_range[0],
                                 step=t['sampletime'],
                                 dimension_list=[0]
                                 )
                 )
    if (outdim == 1):
        c_mode = flap.CoordinateMode(equidistant=False)
        coord.append(flap.Coordinate(name='ADC Channel',
                                     unit='n.a.',
                                     mode=c_mode,
                                     shape=[1],
                                     values=adc_proc[0],
                                     dimension_list=[]
                                     )
                     )
        coord.append(flap.Coordinate(name='Signal name',
                                     unit='n.a.',
                                     mode=c_mode,
                                     shape=[1],
                                     values=chname_proc[0],
                                     dimension_list=[]
                                     )
                     )
    elif (outdim == 2):
        c_mode = flap.CoordinateMode(equidistant=False)
        coord.append(flap.Coordinate(name='ADC Channel',
                                     unit='n.a.',
                                     mode=c_mode,
                                     shape=[len(adc_proc)],
                                     values=np.array(adc_proc),
                                     dimension_list=[1]
                                     )
                     )
        coord.append(flap.Coordinate(name='Signal name',
                                     unit='n.a.',
                                     mode=c_mode,
                                     shape=[len(adc_proc)],
                                     values=np.array(chname_proc),
                                     dimension_list=[1]
                                     )
                     )
    else:
        c_mode = flap.CoordinateMode(equidistant=False)
        c_array = np.ndarray((len(out_row_list),len(out_col_list)),dtype=int)
        for i in range(len(adc_proc)):
            c_array[out_row_index[i],out_col_index[i]] = adc_proc[i]
        coord.append(flap.Coordinate(name='ADC Channel',
                                     unit='n.a.',
                                     mode=c_mode,
                                     shape=c_array.shape,
                                     values=c_array,
                                     dimension_list=[1,2]
                                     )
                     )
        maxlen = 0
        for s in chname_proc:
            if (len(s) > maxlen):
                maxlen = len(s)
        c_array = np.ndarray((len(out_row_list),len(out_col_list)),dtype='<U{:d}'.format(maxlen))
        for i in range(len(chname_proc)):
            c_array[out_row_index[i],out_col_index[i]] = chname_proc[i]
        coord.append(flap.Coordinate(name='Signal name',
                                     unit='n.a.',
                                     mode=c_mode,
                                     shape=c_array.shape,
                                     values=c_array,
                                     dimension_list=[1,2]
                                     )
                     )
        coord.append(flap.Coordinate(name='Row',
                                     unit='n.a.',
                                     mode=c_mode,
                                     shape=[len(out_row_list)],
                                     values=np.array(out_row_list),
                                     dimension_list=[1]
                                     )
                     )
        coord.append(flap.Coordinate(name='Column',
                                     unit='n.a.',
                                     mode=c_mode,
                                     shape=[len(out_col_list)],
                                     values=np.array(out_col_list),
                                     dimension_list=[2]
                                     )
                     )
        
    data_title = camera_family + " data"
    if (data_arr.ndim == 1):
        data_title += " " + chname_proc[0]
    d = flap.DataObject(data_array=data_arr,data_unit=data_unit,
                        coordinates=coord, exp_id=None,data_title=data_title)
    return d


def add_coordinate(data_object, new_coordinates, options=None):
    raise NotImplementedError("Coordinate conversions not implemented yet.")

def register(data_source=None):
    if (data_source is None):
        data_source = 'APDCAM'
    flap.register_data_source(data_source, get_data_func=apdcam_get_data, add_coord_func=add_coordinate)
