# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 15:47:09 2022

Example of starting APDCAM Plot GUI

@author: Sandor Zoletnik, Centre for Energy Research  
         zoletnik.sandor@ek-cer.hu
"""

import flap
import flap_apdcam
import flap_apdcam.apdcam_control as apdcam_control

flap_apdcam.register()

apdcam_control.plot_gui()