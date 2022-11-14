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
        self.camera_type_list, self.camera_version_list_list = apdcam_types_versions()
        self.camera_type_list = ["?"] + self.camera_type_list
        self.camera_version_list = None


        
    def create_widgets(self,parent,plot_background=None):
        self.settings_widg = tk.LabelFrame(parent,bd=2, padx=2, pady=2,relief=tk.GROOVE,text='APDCAM General Settings',bg=plot_background,labelanchor='n')
        self.settings_widg.grid(row=0,column=0,sticky="nsew")
        
        camera_settings_frame = tk.LabelFrame(self.settings_widg,bd=4, padx=2, pady=2,relief=tk.GROOVE,text='Camera selection',bg=plot_background)
        camera_settings_frame.grid(row=0,column=0)
        tk.Label(camera_settings_frame,text='Camera type:',bg=plot_background).grid(row=0,column=0,sticky='e')
        self.camera_select_widg = tk.OptionMenu(camera_settings_frame,self.var_camera_type,*tuple(self.camera_type_list),command=self.camera_type_select)
        self.camera_select_widg.grid(row=0,column=1,sticky='w')
        self.var_camera_type.set(self.camera_type_list[0])
        tk.Label(camera_settings_frame,text='Camera version:',bg=plot_background).grid(row=0,column=2,sticky='e')
        self.camera_version_select_widg = tk.OptionMenu(camera_settings_frame,self.var_camera_version,("n.a"),command=self.camera_version_select)
        self.camera_version_select_widg.grid(row=0,column=3,sticky='w')
        
        self.APDCAM_reset_widg = tk.Button(self.settings_widg,text='FACTORY RESET',\
                                           command=self.APDCAM_reset)
        self.APDCAM_reset_widg.grid(row=0,column=1,sticky='ne')            


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
            
