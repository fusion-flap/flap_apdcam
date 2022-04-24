# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 15:47:09 2022

Example of startting APDCAM GUI

@author: Sandor Zoletnik, Centre for Energy Research  
         zoletnik.sandor@ek-cer.hu
"""

import flap_apdcam.apdcam_control as apdcam_control
import flap_apdcam

flap_apdcam.register()

apdcam_control.gui()