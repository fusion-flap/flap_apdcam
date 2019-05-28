# -*- coding: utf-8 -*-
"""
Created on Fri May 10 18:49:40 2019

@author: Zoletnik
"""

def test_apdcam():
    print("\n------- test storage with APDCAM data --------")
    flap.list_data_objects
    print('**** Reading data')
#   dp = os.path.join('c:/Data/W7-X_ABES/','20181018.003')
    d=flap.get_data('APDCAM',name='ADC[1-9]',
                    coordinates=flap.Coordinate(name='Time',c_range=[5,6]), object_name='ADCs')
    d=flap.get_data('APDCAM',name='ADC23', object_name='ADC23')
    d=flap.get_data('APDCAM',name='ADC24',\
                    coordinates=flap.Coordinate(name='Sample',c_range=[10000,20000]), object_name='ADC24')
    print("**** Storage contents")
    flap.list_data_objects()
    d=flap.get_data_object('ADC23',exp_id='*')
    print("**** Deleting ADC23, exp_id: None")
    flap.delete_data_object('ADC23')
    print("**** Storage contents")
    flap.list_data_objects()

    print("**** Deleting ADC23, exp_id: *")
    flap.delete_data_object('ADC23',exp_id='*')
    print("**** Storage contents")
    flap.list_data_objects()

    print("**** Deleting ADC*, exp_id:*")
    flap.delete_data_object('ADC*',exp_id='*')
    print("**** Storage contents")
    flap.list_data_objects()
