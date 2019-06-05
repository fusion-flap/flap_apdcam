# -*- coding: utf-8 -*-
"""
Created on Fri May 10 18:49:40 2019

@author: Zoletnik
"""
import os
import matplotlib.pyplot as plt

import flap
import flap_apdcam

flap_apdcam.register()

def test_apdcam():
    print("\n------- test storage with APDCAM data --------")
    flap.list_data_objects
    print('**** Reading data')
#   dp = os.path.join('c:/Data/W7-X_ABES/','20181018.003')
    d=flap.get_data('APDCAM',
                    name=['ADC[5-9]','ADC13'],
                    coordinates=flap.Coordinate(name='Time',c_range=[0,0.01]), 
                    object_name='ADCs')
    d=flap.get_data('APDCAM',
                    name='ADC23', 
                    object_name='ADC23')
    d=flap.get_data('APDCAM',
                    name='ADC24',
                    options={'Scaling':'Volt'},
                    coordinates=flap.Coordinate(name='Sample',c_range=[10000,20000]), 
                    object_name='ADC24')
    print("**** Storage contents")
    flap.list_data_objects()

    plt.close('all')
    plt.figure()
    print("**** Plotting all loaded signals as function of time.")
    p1 = flap.plot('ADCs',plot_type='multi xy',axes='Time',options={'Y sep':20000})
    labels = flap.get_data_object('ADCs').coordinate('Signal name',index=[0,...])[0]
    p1.plt_axis_list[0].legend(labels[0])
    print("**** Plotting ADC24 as function of sample number.")
    plt.figure()
    flap.plot('ADC24',axes='Sample')
    
    
# Reading configuration file in the test directory
thisdir = os.path.dirname(os.path.realpath(__file__))
fn = os.path.join(thisdir,"flap_test_apdcam.cfg")
flap.config.read(file_name=fn)
test_apdcam()