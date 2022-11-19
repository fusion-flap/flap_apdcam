# -*- coding: utf-8 -*-
"""
Created on Mon Nov 14 21:31:01 2022

@author: Zoletnik
"""

import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import *

from .apdcam_types_versions import *

class APDCAM_Settings_class:
    """
    This is the class for APDCAM10G settings
    """
    
    def __init__(self,root=None,state=None):
        self.root = root
        self.state = state
        self.camera_type = None
        self.camera_version = None
        self.var_camera_type = tk.StringVar()
        self.var_camera_version = tk.StringVar()
        self.camera_type_list, self.camera_version_list_list = apdcam_types_versions(family='10G')
        self.camera_type_list = ["?"] + self.camera_type_list
        self.camera_version_list = None
        self.var_analog_power = tk.IntVar()
        self.var_analog_power.set(0)
        self.analog_power_state = 0
        self.var_dual_sata = tk.IntVar()
        self.var_dual_sata.set(0)
        self.dual_sata_state = 0
        self.test_pattern_names = ['None',
                                   '10000000000000',
                                   '11111111111111',
                                   '00000000000000',
                                   'Checkerboard',
                                   'Pseudo random long',
                                   'Pseudo random short',
                                   '0-1 word toggle',
                                   'User pattern',
                                   '101010...',
                                   '1x sync',
                                   '1 bit high',
                                   'Mixed frequency'
                                   ]
        self.test_pattern_codes = [0,1,2,3,4,5,6,7,8,9,10,11,12]
        self.var_test_pattern = tk.StringVar()
        self.var_test_pattern.set(self.test_pattern_names[0])
        self.act_test_pattern = 0
        
    def create_widgets(self,parent,plot_background=None):
        settings_frame_widg = tk.LabelFrame(parent,bd=2, padx=2, pady=2,relief=tk.GROOVE,text='APDCAM Settings',bg=plot_background,labelanchor='n')
        settings_frame_widg.grid(row=0,column=0,sticky="nsew")
        
        general_settings_frame_widg = tk.LabelFrame(settings_frame_widg,bd=2, padx=2, pady=2,relief=tk.GROOVE,text='General Settings',bg=plot_background,labelanchor='n')
        general_settings_frame_widg.grid(row=0,column=0,sticky="nsew")
        
        camera_selection_frame_widg = tk.LabelFrame(general_settings_frame_widg,bd=4, padx=2, pady=2,relief=tk.GROOVE,text='Camera selection',bg=plot_background)
        camera_selection_frame_widg.grid(row=0,column=0)
        tk.Label(camera_selection_frame_widg,text='Camera type:',bg=plot_background).grid(row=0,column=0,sticky='e')
        self.camera_select_widg = tk.OptionMenu(camera_selection_frame_widg,self.var_camera_type,*tuple(self.camera_type_list),command=self.camera_type_select)
        self.camera_select_widg.grid(row=0,column=1,sticky='w')
        self.var_camera_type.set(self.camera_type_list[0])
        tk.Label(camera_selection_frame_widg,text='Camera version:',bg=plot_background).grid(row=0,column=2,sticky='e')
        self.camera_version_select_widg = tk.OptionMenu(camera_selection_frame_widg,self.var_camera_version,("n.a"),command=self.camera_version_select)
        self.camera_version_select_widg.grid(row=0,column=3,sticky='w')
        
        self.APDCAM_reset_widg = tk.Button(general_settings_frame_widg,text='FACTORY RESET',\
                                           command=self.APDCAM_reset)
        self.APDCAM_reset_widg.grid(row=0,column=1,sticky='ne')    
        self.dual_sata_widg = tk.Radiobutton(general_settings_frame_widg,text='Dual SATA',padx=20,variable=self.var_dual_sata,
                                                command=self.dual_sata_select,value=1
                                                )        
        self.dual_sata_widg.grid(row=0,column=2,sticky='ne')                 

        camera_settings_frame_widg = tk.LabelFrame(settings_frame_widg,bd=2, padx=2, pady=2,relief=tk.GROOVE,text='Settings',bg=plot_background,labelanchor='n')
        camera_settings_frame_widg.grid(row=1,column=0,sticky="nsew")
        tk.Label(camera_settings_frame_widg,text='Test pattern:',bg=plot_background).grid(row=0,column=0,sticky='e')
        self.test_pattern_widg = tk.OptionMenu(camera_settings_frame_widg,self.var_test_pattern,*self.test_pattern_names,command=self.test_pattern_select)
        self.test_pattern_widg.grid(row=0,column=1,sticky='w')
        
 
        power_temp_frame_widg = tk.LabelFrame(settings_frame_widg,bd=2, padx=2, pady=2,relief=tk.GROOVE,text='Power and temperature',bg=plot_background,labelanchor='n')
        power_temp_frame_widg.grid(row=2,column=0,sticky="nsew")
        self.analog_power_widg = tk.Radiobutton(power_temp_frame_widg,text='Analog power',padx=20,variable=self.var_analog_power,
                                                command=self.analog_power_select,value=1
                                                )        
        self.analog_power_widg.grid(row=0,column=0,sticky='nw')     
       
        self.update()

    def update(self):
        self.camera_type = self.state.config.camera_type
        self.camera_version = self.state.config.camera_version
        try:
            index = self.camera_type_list.index(self.camera_type)
            self.var_camera_type.set(self.camera_type_list[index])
            self.camera_version_list = self.camera_version_list_list[index]
            menu = self.camera_version_select_widg['menu']
            menu.delete("0",tk.END)
            if (len(self.camera_version_list) != 0):
                for i,item in enumerate(self.camera_version_list):
                    menu.add_command(label=str(item),command=tk._setit(self.var_camera_version,str(item),self.camera_version_select)) 
                self.camera_version
                self.var_camera_version.set(self.camera_version_list[0])
                self.camera_version = int(self.var_camera_version.get())
            else:
                self.camera_version = None
                self.var_camera_version.set("n.a")
        except ValueError:
            self.var_camera_type.set(self.camera_type_list[0])
            menu = self.camera_version_select_widg['menu']
            menu.delete("0",tk.END)
            self.camera_version = None
            self.var_camera_version.set("n.a")
        try:
            index = self.camera_version_list.index(str(self.camera_version))
            self.var_camera_version.set(self.camera_version_list[index])
        except (ValueError,AttributeError):
            pass
        if (self.state.APDCAM_connected):
            n_adc = len(self.state.APDCAM_reg.status.ADC_address)
            err, d = self.state.APDCAM_reg.getAnalogPower()
            if (err != ""):
                self.state.GUI.add_message(err)
                return
            self.var_analog_power.set(d)
            self.analog_power_state = d
            err,d = self.state.APDCAM_reg.getDualSATA()  
            if (err != ""):
                self.state.GUI.add_message(err)
                return
            if (d):
                self.var_dual_sata.set(1)
                self.dual_sata_state = 1
            else:
                self.var_dual_sata.set(0)
                self.dual_sata_state = 0              
            err,d = self.state.APDCAM_reg.getTestPattern()  
            if (err != ""):
                self.state.GUI.add_message(err)
                return
            for i_adc in range(n_adc):
                for i in range(1,4):
                    if (d[i_adc][i] != d[i_adc][0]):
                        self.state.GUI.add_message("Warning: Different test pattern settings in ADC board #{:d}".format(i_adc + 1))
            for i_adc in range(1,n_adc):
                if (d[i_adc][0] != d[0][0]):
                    self.state.GUI.add_message("Warning: Different test pattern settings in ADC boards. Using board 1 value.")
            self.var_test_pattern.set(self.test_pattern_names[d[0][0]])
            self.act_test_pattern = d[0][0]
            
    
    def camera_type_select(self,event):
        """
        Camera type select widget. Sets the version select widget menu according to the camera versions

        Parameters
        ----------
        event : n.a.
            Not used, required by tk

        Returns
        -------
        None.

        """
        self.camera_type = self.var_camera_type.get()
        index = self.camera_type_list.index(self.camera_type)
        if (index == 0):
            self.camera_type = None
        self.state.config.camera_type = self.camera_type
        
        self.update()
        
    def camera_version_select(self,event):
        if (self.camera_type is None):
            self.camera_version = None
        else:
            self.camera_version = int(self.var_camera_version.get())
        self.state.config.camera_version = self.camera_version

    def APDCAM_reset(self):
        if (not self.state.APDCAM_connected):
            return
        v= tk.messagebox.askokcancel("Warning", "Do you really want to reset factory defaults?\n After reset camera will be at 10.123.13.102", default=tk.messagebox.OK)
        if (v == False):
            return
        self.state.APDCAM_reg.FactoryReset(True)
        self.update()
            
    def analog_power_select(self):
        if (not self.state.APDCAM_connected):
            self.var_analog_power.set(self.analog_power_state)
            return

        if (self.analog_power_state == 0):
            err = self.state.APDCAM_reg.setAnalogPower(1)
            if (err != ""):
                self.state.GUI.add_message(err)
                self.var_analog_power.set(self.analog_power_state)
                return
            self.var_analog_power.set(1)
            self.analog_power_state = 1
        else:
            err = self.state.APDCAM_reg.setAnalogPower(0)
            if (err != ""):
                self.state.GUI.add_message(err)
                self.var_analog_power.set(self.analog_power_state)
                return
            self.var_analog_power.set(0)
            self.analog_power_state = 0
            
    def dual_sata_select(self):
        if (not self.state.APDCAM_connected):
            self.var_dual_sata.set(self.dual_sata_state)
            return
        v= tk.messagebox.askokcancel("Warning", "Do you really want to change dual SATA setting?\n It is related to internal camera configuration.", default=tk.messagebox.OK)
        if (v == False):
            self.var_dual_sata.set(self.dual_sata_state)
            return
        if (self.dual_sata_state == 0):
            err = self.state.APDCAM_reg.setDualSATA(dual_SATA_state=True)
            if (err != ""):
                self.state.GUI.add_message(err)
                self.var_dual_sata.set(self.dual_sata_state)
                return
            self.var_dual_sata.set(1)
            self.dual_sata_state = 1
        else:
            err = self.state.APDCAM_reg.setDualSATA(dual_SATA_state=False)
            if (err != ""):
                self.state.GUI.add_message(err)
                self.var_dual_sata.set(self.dual_sata_state)
                return
            self.var_dual_sata.set(0)
            self.dual_sata_state = 0

    def test_pattern_select(self,event):
        if (not self.state.APDCAM_connected):
            self.var_test_pattern.set(self.test_pattern_names[self.test_pattern_codes.index(self.act_test_pattern)])
            return
        code = self.test_pattern_codes[self.test_pattern_names.index(self.var_test_pattern.get())]
        err = self.state.APDCAM_reg.setTestPattern(code)
        if (err != ""):
            self.state.GUI.add_message(err)
            self.var_test_pattern.set(self.test_pattern_names[self.test_pattern_codes.index(self.act_test_pattern)])
            return
        self.act_test_pattern = code
