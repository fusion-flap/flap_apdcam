#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 18 22:50:29 2022

@author: Sandor Zoletnik, Centre for Energy Research  
         zoletnik.sandor@ek-cer.hu
"""
import flap_apdcam
flap_apdcam.register()
import flap_apdcam.apdcam_control as apd
apd.gui()