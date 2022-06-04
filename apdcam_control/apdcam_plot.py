# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 22:23:47 2022

GUI for plotting APDCAM data

@author: Sandor Zoletnik, Centre for Energy Research  
         zoletnik.sandor@ek-cer.hu
"""
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import *
import os
import threading

import flap

import matplotlib.pyplot as plt
from .apdcam_types_versions import *

class APDCAM_Plot_class:
    """
    This is the class doing everything
    """
    
    def __init__(self,root=None):
        self.root = root
        self.var_shotID = tk.StringVar()
        self.var_shotID.set(value="")
        self.var_figure = tk.StringVar()
        self.figure_list = ['New figure']
        self.plotID_list = [None]
        self.legend_list = [None]
        self.var_signals = tk.StringVar()
        self.var_signals.set('APD-*')
        plt.close('all')
        self.figsize=(20,15)
        self.var_end_time = tk.StringVar()
        self.var_end_time.set(value="")      
        self.var_start_time = tk.StringVar()
        self.var_end_time.set(value="")
        self.plot_type_list = ['xy','grid xy','image','anim-image']
        self.plot_type = tk.StringVar()
        self.plot_type.set(self.plot_type_list[0])
        self.data = None
        self.var_camera_type = tk.StringVar()
        self.var_camera_version = tk.StringVar()
        self.camera_type_list, self.camera_version_list_list = apdcam_types_versions()
        self.camera_version_list = None
        self.var_rawplot_options_allpoints = tk.IntVar()
        self.rawplot_options_allpoints = False
        self.var_rawplot_options_autoscale = tk.IntVar()
        self.rawplot_options_autoscale = False
        self.var_rawplot_options_yrange1 = tk.StringVar()
        self.var_rawplot_options_yrange1.set(str(0))
        self.var_rawplot_options_yrange2= tk.StringVar()
        self.var_rawplot_options_yrange2.set(str(16384))
        self.splot_type_list = ['xy','grid xy','image','anim-image']
        self.splot_type = tk.StringVar()
        self.splot_type.set(self.splot_type_list[0])
        self.var_spectrplot_options_allpoints = tk.IntVar()
        self.spectrplot_options_allpoints = False
        self.var_spectrplot_options_autoscale = tk.IntVar()
        self.spectrplot_options_autoscale = False
        self.var_spectrplot_options_yrange1 = tk.StringVar()
        self.var_spectrplot_options_yrange1.set(str(0))
        self.var_spectrplot_options_yrange2= tk.StringVar()
        self.var_spectrplot_options_yrange2.set("{:4.2e}".format(1e5))
        self.var_spectrplot_options_logfres = tk.IntVar()
        self.spectrplot_options_logfres = True
        self.var_spectrplot_options_fres = tk.StringVar()
        self.var_spectrplot_options_frange1 = tk.StringVar()
        self.var_spectrplot_options_frange2 = tk.StringVar()
        self.var_spectrplot_options_logy = tk.IntVar()
        self.var_spectrplot_options_logx = tk.IntVar()
        
    def create_widgets(self,parent,config_file=None,camera_type=None,camera_version=None,plot_background=None):
        self.camera_type = camera_type
        self.camera_version = camera_version
        if (config_file is not None):
            flap.config.read(file_name=config_file)
        self.config_file = config_file
        self.plotControl_widg = tk.LabelFrame(parent,bd=2, padx=2, pady=2,relief=tk.GROOVE,text='Plot control',bg=plot_background,labelanchor='n')
        self.plotControl_widg.grid(row=0,column=0)
        
        row0 = 0
        if ((camera_type is None) or (camera_version is None)):
            camera_settings_frame = tk.LabelFrame(self.plotControl_widg,bd=4, padx=2, pady=2,relief=tk.GROOVE,text='Camera selection',bg=plot_background)
            camera_settings_frame.grid(row=0,column=0)
            if (camera_type is None):
                w = tk.Label(camera_settings_frame,text='Camera type:',bg=plot_background).grid(row=0,column=0,sticky='e')
                self.camera_select_widg = tk.OptionMenu(camera_settings_frame,self.var_camera_type,*tuple(self.camera_type_list),command=self.camera_type_select)
                self.camera_select_widg.grid(row=0,column=1,sticky='w')
            if (camera_version is None):
                w = tk.Label(camera_settings_frame,text='Camera version:',bg=plot_background).grid(row=0,column=2,sticky='e')
                self.camera_version_select_widg = tk.OptionMenu(camera_settings_frame,self.var_camera_version,("n.a"),command=self.camera_version_select)
                self.camera_version_select_widg.grid(row=0,column=3,sticky='w')
        else:
            camera_settings_frame = tk.LabelFrame(self.plotControl_widg,bd=4, padx=2, pady=2,relief=tk.GROOVE,text='Camera selection',bg=plot_background)
            camera_settings_frame.grid(row=0,column=0)
            row0 = 1
            if (camera_type is None):
                w = tk.Label(camera_settings_frame,text='Camera type:',bg=plot_background).grid(row=0,column=0,sticky='e')
                self.camera_select_widg = tk.OptionMenu(camera_settings_frame,self.var_camera_type,*tuple(self.camera_type_list),command=self.camera_type_select)
                self.camera_select_widg.grid(row=0,column=1,sticky='w')
            else:
                w = tk.Label(camera_settings_frame,text='Camera type:'+str(camera_type),bg=plot_background).grid(row=0,column=0)
            if (camera_version is None):
                w = tk.Label(camera_settings_frame,text='      Camera version:',bg=plot_background).grid(row=0,column=2,sticky='e')
                self.camera_version_select_widg = tk.OptionMenu(camera_settings_frame,self.var_camera_version,("n.a"),command=self.camera_version_select)
                self.camera_version_select_widg.grid(row=0,column=3,sticky='w')
            else:
                w = tk.Label(camera_settings_frame,text='      Camera version: {:s}'.format(str(camera_version)),bg=plot_background).grid(row=0,column=2)
        row0 = 1            
                
        general_settings_frame = tk.LabelFrame(self.plotControl_widg,bd=4, padx=2, pady=2,relief=tk.GROOVE,text='Data',bg=plot_background)
        general_settings_frame.grid(row=row0,column=0)
        w = tk.Label(general_settings_frame,text='Measurement dir:',bg=plot_background).grid(row=0,column=0,sticky='e')
        self.shotID_widg = tk.Entry(general_settings_frame,width=70,textvariable=self.var_shotID,bg=plot_background)
        self.shotID_widg.grid(row=0,column=1,columnspan=2,sticky='w')
        signals_frame = tk.Frame(general_settings_frame)
        signals_frame.grid(row=1,column=0) 
        w = tk.Label(signals_frame,text='Signals:',bg=plot_background).grid(row=0,column=0,sticky='e')
        self.signals_widg = tk.Entry(signals_frame,width=10,textvariable=self.var_signals,bg=plot_background)
        self.signals_widg.grid(row=0,column=1,sticky='e')
        time_frame = tk.Frame(general_settings_frame,bg=plot_background)
        time_frame.grid(row=1,column=1)
        w = tk.Label(time_frame,text='Timerange[s]:',bg=plot_background).grid(row=0,column=0,sticky='e')
        self.start_time_widg = tk.Entry(time_frame,width=10,textvariable=self.var_start_time,bg=plot_background)
        self.start_time_widg.grid(row=0,column=1,sticky='e')
        w = tk.Label(time_frame,text='-',bg=plot_background).grid(row=0,column=2,sticky='e')
        self.end_time_widg = tk.Entry(time_frame,width=10,textvariable=self.var_end_time,bg=plot_background)
        self.end_time_widg.grid(row=0,column=3,sticky='w')
        self.getdata_widg = tk.Button(general_settings_frame,command=self.getdata,text='GET DATA',bg=plot_background)
        self.getdata_widg .grid(row=1,column=2,columnspan=2,sticky='w')
        
        self.message_widg = tk.Text(general_settings_frame,font=('Times','10'),height=6,width=80,bg=plot_background)
        self.message_widg.grid(row=2,column=0,columnspan=4)  
        
        figure_frame = tk.Frame(self.plotControl_widg)
        figure_frame.grid(row=row0+1,column=0,sticky='e')
        w = tk.Label(figure_frame,text='Figure:',bg=plot_background).grid(row=0,column=0,sticky='e')
        self.figure_select_widg = tk.OptionMenu(figure_frame,self.var_figure,*tuple(self.figure_list),command=self.figure_select)
        self.figure_select_widg.grid(row=0,column=1,sticky='w')
        self.var_figure.set(self.figure_list[0])
        
        self.root.update()
        pwidth = general_settings_frame.winfo_width()
        #---------------- Raw signal plots --------------
        self.rawplot_widg = tk.LabelFrame(self.plotControl_widg,bd=4, padx=2, pady=2,relief=tk.GROOVE,text='Raw data plot',bg=plot_background) 
        self.rawplot_widg.grid(row=row0 + 2,column=0,columnspan=4)
        self.rawplot_button_widg = tk.Button(self.rawplot_widg,command=self.rawplot,text='PLOT',bg=plot_background)
        self.rawplot_button_widg.grid(row=0,column=0,sticky='n')
        raw_plottype_frame = tk.Frame(self.rawplot_widg,bg=plot_background)
        raw_plottype_frame.grid(row=0,column=1,sticky='n')
        w = tk.Label(raw_plottype_frame,text='Plot type',bg=plot_background).grid(row=0,column=0,sticky='s')
        self.plot_type_select_widg = tk.OptionMenu(raw_plottype_frame,self.plot_type,*tuple(self.plot_type_list),command=self.plot_type_select)
        self.plot_type_select_widg.grid(row=1,column=0,sticky='n')
        
        rawplot_options_widg = tk.Frame(self.rawplot_widg,bg=plot_background,bd=4, padx=2, pady=2,relief=tk.GROOVE)
        rawplot_options_widg.grid(row=0,column=3)
        w = tk.Label(rawplot_options_widg,text='  Plot options    ',bg=plot_background).grid(row=0,column=0)
        self.raw_option_allpoints = tk.Radiobutton(rawplot_options_widg,text='Plot all points',padx=20,variable=self.var_rawplot_options_allpoints,
                                                   command=self.raw_options_allpoints_func,value=1
                                                   )
        self.var_rawplot_options_allpoints.set(0)
        self.raw_option_allpoints.grid(row=0,column=1,sticky='w')
        self.raw_option_autoscale = tk.Radiobutton(rawplot_options_widg,text='Autoscale signal',padx=20,variable=self.var_rawplot_options_autoscale,
                                                   command=self.raw_options_autoscale_func,value=1
                                                   )
        self.var_rawplot_options_autoscale.set(0)
        self.raw_option_autoscale.grid(row=2,column=1,sticky='w')
        rawplot_yscale_frame_widg = tk.Frame(rawplot_options_widg,bg=plot_background)
        rawplot_yscale_frame_widg.grid(row=3,column=1)
        w = tk.Label(rawplot_yscale_frame_widg,text='Signal range:',bg=plot_background).grid(row=0,column=0,sticky='e')
        self.rawplot_yscale1_widg = tk.Entry(rawplot_yscale_frame_widg,width=10,textvariable=self.var_rawplot_options_yrange1,bg=plot_background)
        self.rawplot_yscale1_widg.grid(row=0,column=1,sticky='e')
        w = tk.Label(rawplot_yscale_frame_widg,text='-',bg=plot_background).grid(row=0,column=2,sticky='e')
        self.rawplot_yscale2_widg = tk.Entry(rawplot_yscale_frame_widg,width=10,textvariable=self.var_rawplot_options_yrange2,bg=plot_background)
        self.rawplot_yscale2_widg .grid(row=0,column=3,sticky='w')

        self.root.update()
        pheight = self.rawplot_widg.winfo_height()
        self.rawplot_widg.config(width=pwidth)
        self.rawplot_widg.config(height=pheight)
        self.rawplot_widg.grid_propagate(0)

        #---------------- Spectrum signal plots --------------
        self.spectrplot_widg = tk.LabelFrame(self.plotControl_widg,bd=4, padx=2, pady=2,relief=tk.GROOVE,text='Spectrum plot',bg=plot_background)
        self.spectrplot_widg.grid(row=row0 + 3,column=0,columnspan=4)
        self.spectrplot_button_widg = tk.Button(self.spectrplot_widg,command=self.spectrplot,text='PLOT',bg=plot_background)
        self.spectrplot_button_widg.grid(row=0,column=0,sticky='n')
        
        spectr_plottype_frame = tk.Frame(self.spectrplot_widg,bg=plot_background)
        spectr_plottype_frame.grid(row=0,column=1,sticky='n')
        w = tk.Label(spectr_plottype_frame,text='Plot type',bg=plot_background).grid(row=0,column=0,sticky='s')
        self.splot_type_select_widg = tk.OptionMenu(spectr_plottype_frame,self.splot_type,*tuple(self.splot_type_list),command=self.splot_type_select)
        self.splot_type_select_widg.grid(row=1,column=0,sticky='n')
        
        spectrplot_options_widg = tk.Frame(self.spectrplot_widg,bg=plot_background,bd=4, padx=2, pady=2,relief=tk.GROOVE)
        spectrplot_options_widg.grid(row=0,column=3,sticky='e')
        w = tk.Label(spectrplot_options_widg,text='Spectrum options    ').grid(row=0,column=0)
        fres_widg = tk.Frame(spectrplot_options_widg,bg=plot_background)
        fres_widg.grid(row=0,column=1,sticky='w')
        w = tk.Label(fres_widg,text='Frequency resolution [Hz]:',bg=plot_background).grid(row=0,column=0,sticky='e')
        self.spectrplot_fres_widg = tk.Entry(fres_widg,width=10,textvariable=self.var_spectrplot_options_fres,bg=plot_background)
        self.spectrplot_fres_widg.grid(row=0,column=1,sticky='e')
        try:
            self.var_spectrplot_options_fres.set("{:4.2e}".format(float(flap.config.get('PS','Resolution',default='1e3'))))
        except ValueError:
            self.var_spectrplot_options_fres.set("1E3")
        self.spectrum_option_logfres = tk.Radiobutton(spectrplot_options_widg,text='Log. freqency resolution',padx=20,variable=self.var_spectrplot_options_logfres,
                                                   command=self.spectrplot_options_logfres_func,value=1
                                                   )
        val = flap.config.interpret_config_value(flap.config.get('PS','Logarithmic',default='True'))
        if (type(val) == bool):
            self.spectrplot_options_logfres = val
        else:
            self.spectrplot_options_logfres = True
        if (self.spectrplot_options_logfres):
            self.var_spectrplot_options_logfres.set(1)
        else:
            self.var_spectrplot_options_logfres.set(0)
        self.spectrum_option_logfres.grid(row=1,column=1,sticky='e')
        
        spectrplot_frange_frame_widg = tk.Frame(spectrplot_options_widg,bg=plot_background)
        spectrplot_frange_frame_widg.grid(row=2,column=1)
        w = tk.Label(spectrplot_frange_frame_widg,text='Frequency range [Hz]:',bg=plot_background).grid(row=0,column=0,sticky='e')
        self.spectrplot_frange1_widg = tk.Entry(spectrplot_frange_frame_widg,width=10,textvariable=self.var_spectrplot_options_frange1,bg=plot_background)
        self.spectrplot_frange1_widg.grid(row=0,column=1,sticky='e')
        w = tk.Label(spectrplot_frange_frame_widg,text='-',bg=plot_background).grid(row=0,column=2,sticky='e')
        self.spectrplot_frange2_widg = tk.Entry(spectrplot_frange_frame_widg,width=10,textvariable=self.var_spectrplot_options_frange2,bg=plot_background)
        self.spectrplot_frange2_widg .grid(row=0,column=3,sticky='w')

        val = flap.config.interpret_config_value(flap.config.get('PS','Range',default='[1e3,1e6]'))
        if (type(val) is list):
            try:
                f1 = float(val[0])
                f2 = float(val[1])
            except ValueError:
                f1=1e3
                f2=1e6
        else:
                f1=1e3
                f2=1e6
        self.var_spectrplot_options_frange1.set("{:4.2e}".format(f1))
        self.var_spectrplot_options_frange2.set("{:4.2e}".format(f2))
        
        spectrplot_plotoptions_widg = tk.Frame(self.spectrplot_widg,bg=plot_background,bd=4, padx=2, pady=2,relief=tk.GROOVE)
        spectrplot_plotoptions_widg.grid(row=1,column=3)
        w = tk.Label(spectrplot_plotoptions_widg,text='   Plot options    ',bg=plot_background).grid(row=0,column=0)
        spectrplot_yscale_frame_widg = tk.Frame(spectrplot_plotoptions_widg,bg=plot_background)
        spectrplot_yscale_frame_widg.grid(row=0,column=1,sticky='w')
        w = tk.Label(spectrplot_yscale_frame_widg,text='Power range:',bg=plot_background).grid(row=0,column=0,sticky='e')
        self.spectrplot_yscale1_widg = tk.Entry(spectrplot_yscale_frame_widg,width=10,textvariable=self.var_spectrplot_options_yrange1,bg=plot_background)
        self.spectrplot_yscale1_widg.grid(row=0,column=1,sticky='e')
        w = tk.Label(spectrplot_yscale_frame_widg,text='-',bg=plot_background).grid(row=0,column=2,sticky='e')
        self.spectrplot_yscale2_widg = tk.Entry(spectrplot_yscale_frame_widg,width=10,textvariable=self.var_spectrplot_options_yrange2,bg=plot_background)
        self.spectrplot_yscale2_widg .grid(row=0,column=3,sticky='w')
    
        self.spectrum_option_autoscale = tk.Radiobutton(spectrplot_plotoptions_widg,text='Autoscale power',padx=20,variable=self.var_spectrplot_options_autoscale,
                                                   command=self.spectrplot_options_autoscale_func,value=1
                                                   )
        self.var_spectrplot_options_autoscale.set(0)
        self.spectrum_option_autoscale.grid(row=1,column=1,sticky='e')
        
        self.spectrum_option_allpoints = tk.Radiobutton(spectrplot_plotoptions_widg,text='Plot all points',padx=20,variable=self.var_spectrplot_options_allpoints,
                                                   command=self.spectrplot_options_allpoints_func,value=1
                                                   )
        self.var_spectrplot_options_allpoints.set(0)
        self.spectrplot_options_allpoints = False
        self.spectrum_option_allpoints.grid(row=2,column=1,sticky='w')
        
        self.spectrum_option_logx = tk.Radiobutton(spectrplot_plotoptions_widg,text='Log x',padx=20,variable=self.var_spectrplot_options_logx,
                                                   command=self.spectrplot_options_logx_func,value=1
                                                   )
        val = flap.config.interpret_config_value(flap.config.get('Plot','Log x',default='True'))
        if (type(val) == bool):
            self.spectrplot_options_logx = val
        else:
            self.spectrplot_options_logx = True
        if (self.spectrplot_options_logx):
            self.var_spectrplot_options_logx.set(1)
        else:
            self.var_spectrplot_options_logx.set(0)
        self.spectrum_option_logx.grid(row=3,column=1,sticky='w')
        
        self.spectrum_option_logy = tk.Radiobutton(spectrplot_plotoptions_widg,text='Log y',padx=20,variable=self.var_spectrplot_options_logy,
                                                   command=self.spectrplot_options_logy_func,value=1
                                                   )
        val = flap.config.interpret_config_value(flap.config.get('Plot','Log y',default='True'))
        if (type(val) == bool):
            self.spectrplot_options_logy = val
        else:
            self.spectrplot_options_logy = True
        if (self.spectrplot_options_logy):
            self.var_spectrplot_options_logy.set(1)
        else:
            self.var_spectrplot_options_logy.set(0)
        self.spectrum_option_logy.grid(row=4,column=1,sticky='w')
        
        self.root.update()
        pheight = self.spectrplot_widg.winfo_height()
        self.spectrplot_widg.config(width=pwidth)
        self.spectrplot_widg.config(height=pheight)
        self.spectrplot_widg.grid_propagate(0)

        
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
        self.camera_version_list = self.camera_version_list_list[index]
        menu = self.camera_version_select_widg['menu']
        menu.delete("0",tk.END)
        if (len(self.camera_version_list) != 0):
            for i,item in enumerate(self.camera_version_list):
                menu.add_command(label=str(item),command=tk._setit(self.var_camera_version,str(item),self.camera_version_select)) 
            self.var_camera_version.set(self.camera_version_list[0])
            self.camera_version = int(self.var_camera_version.get())
        else:
            self.camera_version = None
            self.var_camera_version.set("n.a")
        
    def camera_version_select(self,event):
        if (self.camera_type is None):
            return
        self.camera_version = int(self.var_camera_version.get())

        
    def figure_select(self,event):
        """
        This is called when the figure select widget is activated.
        If menu 0 is selected a new figure is created.
        If a figure is selected which has been delated, creates it.
        Handles the plotIDs for the flap.plot method, so as overplots are handled correctly.

        Parameters
        ----------
        event : n.a.
            Not used, required by tk.

        Returns
        -------
        None.

        """
        if (event is None):
            if (len(plt.get_fignums()) == 0):
                self.var_figure.set(self.figure_list[0])
                self.figure_list = [self.figure_list[0]]
                self.plotID_list = [None]
        if (self.var_figure.get() == self.figure_list[0]):
            plt.figure(figsize=self.figsize)
            self.figure_list.append(str(plt.gcf().number))
            self.act_plotID = None
            self.plotID_list.append(None)
            self.legend_list.append([])
        else:
            try:
                plt.get_fignums().index(int(self.var_figure.get()))
                plt.figure(int(self.var_figure.get()))
            except ValueError:
                plt.figure(int(self.var_figure.get()),figsize=self.figsize)
                self.plotID_list[int(self.var_figure.get())] = None
                self.legend_list[int(self.var_figure.get())] = []
        menu = self.figure_select_widg['menu']
        menu.delete("0",tk.END)
        for i,item in enumerate(self.figure_list):
            menu.add_command(label=item,command=tk._setit(self.var_figure,item,self.figure_select))
        self.var_figure.set(self.figure_list[plt.gcf().number])
        self.act_plotID = self.plotID_list[plt.gcf().number]
            
    def plot_type_select(self,event):
        """
        Raw data plot type select. Does nothing

        Parameters
        ----------
        event : n.a.
            Not used, required by tk.

        Returns
        -------
        None.

        """
        pass  

    def splot_type_select(self,event):
        """
        Spectrum plot type select. Does nothing

        Parameters
        ----------
        event : n.a.
            Not used, required by tk.

        Returns
        -------
        None.

        """
        pass  

    def raw_options_allpoints_func(self):
        """
        Callback function for raw plot allpoints radiobutton.

        Returns
        -------
        None.

        """
        if (not self.rawplot_options_allpoints):
            self.var_rawplot_options_allpoints.set(1)
            self.rawplot_options_allpoints = True
        else:
            self.var_rawplot_options_allpoints.set(0)
            self.rawplot_options_allpoints = False
          
    def spectrplot_options_allpoints_func(self):
        """
        Callback function for spectrum plot allpoints radiobutton.

        Returns
        -------
        None.

        """
        if (not self.spectrplot_options_allpoints):
            self.var_spectrplot_options_allpoints.set(1)
            self.spectrplot_options_allpoints = True
        else:
            self.var_spectrplot_options_allpoints.set(0)
            self.spectrplot_options_allpoints = False

    def spectrplot_options_logfres_func(self):
        """
        Callback function for sectrum plot logarithmic fres radiobutton.

        Returns
        -------
        None.

        """
        if (not self.spectrplot_options_logfres):
            self.var_spectrplot_options_logfres.set(1)
            self.spectrplot_options_logfres = True
        else:
            self.var_spectrplot_options_logfres.set(0)
            self.spectrplot_options_logfres = False
            
    def spectrplot_options_logx_func(self):
        """
        Callback function for spectrum plot log x radiobutton.

        Returns
        -------
        None.

        """
        if (not self.spectrplot_options_logx):
            self.var_spectrplot_options_logx.set(1)
            self.spectrplot_options_logx = True
        else:
            self.var_spectrplot_options_logx.set(0)
            self.spectrplot_options_logx = False

    def spectrplot_options_logy_func(self):
        """
        Callback function for spectrum plot log y radiobutton.

        Returns
        -------
        None.

        """
        if (not self.spectrplot_options_logy):
            self.var_spectrplot_options_logy.set(1)
            self.spectrplot_options_logy = True
        else:
            self.var_spectrplot_options_logy.set(0)
            self.spectrplot_options_logy = False
            
    def raw_options_autoscale_func(self):        
        """
        Callback function for raw signal plot autoscale radiobutton.

        Returns
        -------
        None.

        """
        if (not self.rawplot_options_autoscale):
            self.var_rawplot_options_autoscale.set(1)
            self.rawplot_options_autoscale = True
            self.rawplot_yscale1_widg['state'] = tk.DISABLED
            self.rawplot_yscale2_widg['state'] = tk.DISABLED           
        else:
            self.var_rawplot_options_autoscale.set(0)
            self.rawplot_options_autoscale = False
            self.rawplot_yscale1_widg['state'] = tk.NORMAL
            self.rawplot_yscale2_widg['state'] = tk.NORMAL           

    def spectrplot_options_autoscale_func(self):        
        """
        Callback function for spectrum plot power autoscale radiobutton.

        Returns
        -------
        None.

        """
        if (not self.spectrplot_options_autoscale):
            self.var_spectrplot_options_autoscale.set(1)
            self.spectrplot_options_autoscale = True
            self.spectrplot_yscale1_widg['state'] = tk.DISABLED
            self.spectrplot_yscale2_widg['state'] = tk.DISABLED           
        else:
            self.var_spectrplot_options_autoscale.set(0)
            self.spectrplot_options_autoscale = False
            self.spectrplot_yscale1_widg['state'] = tk.NORMAL
            self.spectrplot_yscale2_widg['state'] = tk.NORMAL           

    def start_rawplot(self):
        self.rawplotThread = threading.Thread(target=self.rawplot)
        self.rawplotThread.start()
        
    def rawplot(self):
        """
        Callback function for raw signal plots.

        Returns
        -------
        None.

        """
        # plt.figure()
        # plt.plot([1,2,4])
        # plt.ion()
        # plt.show()
        # plt.pause(5)
        # return
        if (self.data is None):
            self.add_message("Cannot plot, load data first.")  
            return
        self.figure_select(None)
        plot_type = self.plot_type.get()
        options = {}
        options['All points'] = self.rawplot_options_allpoints
        options['Log x'] = False
        options['Log y'] = False        
        if (plot_type == 'xy'):
            if (self.data.data.ndim != 1):
                self.add_message("'xy plot' is applicable only for a single channel like APD-2-3.")  
                return
            if (not self.rawplot_options_autoscale):
                options['Y range'] = [float(self.var_rawplot_options_yrange1.get()),float(self.var_rawplot_options_yrange2.get())]
            try:
                plot_id = self.data.plot(plot_type=plot_type,axes=['Time'],plot_id=self.act_plotID,
                                         options=options
                                         )
            except ValueError as e:
                self.add_message("Error: {:s}".format(str(e)))
                return
            self.legend_list[plt.gcf().number].append(self.data.data_title)
            plt.legend(self.legend_list[plt.gcf().number])
        elif (plot_type == 'grid xy'):
            if (self.data.data.ndim != 3):
                self.add_message("'grid xy' plot is applicable only for a 2D channel matrix.")  
                return
            if (not self.rawplot_options_autoscale):
                options['Y range'] = [float(self.var_rawplot_options_yrange1.get()),float(self.var_rawplot_options_yrange2.get())]
            try:
                plot_id = self.data.plot(plot_type=plot_type,axes=['Row','Column','Time'],plot_id=self.act_plotID,
                                         options=options
                                         )
            except ValueError as e:
                self.add_message("Error: {:s}".format(str(e)))
                return                
        elif (plot_type == 'image'):
            if (self.data.data.ndim != 3):
                self.add_message("'image' plot is applicable only for a 2D channel matrix.")  
                return
            if (not self.rawplot_options_autoscale):
                options['Z range'] = [float(self.var_rawplot_options_yrange1.get()),float(self.var_rawplot_options_yrange2.get())]
            try:
                plot_id = self.data.plot(plot_type=plot_type,
                                         summing={'Time':'Mean'},axes=['Row','Column'],plot_id=self.act_plotID,
                                         options=options
                                         )
            except (ValueError,TypeError) as e:
                self.add_message("Error: {:s}".format(str(e)))
                return                
        elif (plot_type == 'anim-image'):
            if (self.data.data.ndim != 3):
                self.add_message("'anim-image' plot is applicable only for a 2D channel matrix.")  
                return
            if (not self.rawplot_options_autoscale):
                options['Z range'] = [float(self.var_rawplot_options_yrange1.get()),float(self.var_rawplot_options_yrange2.get())]
            options['Wait'] = 0.01
            try:
                plot_id = self.data.plot(plot_type=plot_type,
                                         axes=['Row','Column','Time'],plot_id=self.act_plotID,
                                         options=options
                                         )
            except (ValueError,TypeError) as e:
                self.add_message("Error: {:s}".format(str(e)))
                return                
        else:
            self.add_message("'{:s}' plot not implemented yet.".format(plot_type)) 
            return
        plt.show()
        plt.pause(0.05)
        self.plotID_list[plt.gcf().number] = flap.get_plot_id()
        self.act_plotID = flap.get_plot_id()
        self.add_message("Plot done for {:s}.".format(self.data.data_title))  

    def spectrplot(self):
        """
        Callback function for spectrum plots.

        Returns
        -------
        None.

        """
        if (self.data is None):
            self.add_message("Cannot plot, load data first.")  
            return
        plot_type = self.splot_type.get()
        if (plot_type == 'xy'):
            if (self.data.data.ndim != 1):
                self.add_message("'xy plot' is applicable only for a single channel like APD-2-3.")  
                return
        elif (plot_type == 'grid xy'):
            if (self.data.data.ndim != 3):
                self.add_message("'grid xy' plot is applicable only for a 2D channel matrix.")  
                return
        elif (plot_type == 'image'):
            if (self.data.data.ndim != 3):
                self.add_message("'image' plot is applicable only for a 2D channel matrix.")  
                return
        elif (plot_type == 'anim-image'):
            if (self.data.data.ndim != 3):
                self.add_message("'anim-image' plot is applicable only for a 2D channel matrix.")  
                return
        else:
            self.add_message("'{:s}' plot not implemented yet.".format(plot_type)) 
            return

        self.figure_select(None)
        
        options = {}
        options['All points'] = self.spectrplot_options_allpoints
        options['Log x'] = self.spectrplot_options_logx
        options['Log y'] = self.spectrplot_options_logy
        power_options = {}
        try:
            power_options['Resolution'] = float(self.var_spectrplot_options_fres.get())
        except ValueError:
            self.add_message("Invalid frequency resolution.")  
            return
        try:
            f1 = float(self.var_spectrplot_options_frange1.get())
            f2 = float(self.var_spectrplot_options_frange2.get())
            power_options['Range'] = [f1,f2]
        except ValueError:
            self.add_message("Invalid frequency range.")  
            return
        power_options['Logarithmic'] = self.spectrplot_options_logfres
        self.add_message("Calculating spectra...")
        root.update()
        try:
            psdata = self.data.apsd(coordinate='Time',options=power_options)
        except Exception as e:
            self.add_message("Error in spectrum calculation:{:s}".format(str(e)))  
            return
        self.add_message("   ...done") 
        root.update()
        plotrange = [float(self.var_spectrplot_options_yrange1.get()),float(self.var_spectrplot_options_yrange2.get())]
        if (plot_type == 'xy'):
            if (self.data.data.ndim != 1):
                self.add_message("'xy plot' is applicable only for a single channel like APD-2-3.")  
                return
            if (not self.spectrplot_options_autoscale):
                options['Y range'] = plotrange
            try:
                plot_id = psdata.plot(plot_type=plot_type,axes=['Frequency'],plot_id=self.act_plotID,
                                      options=options
                                      )
            except ValueError as e:
                self.add_message("Error: {:s}".format(str(e)))
                return
            self.legend_list[plt.gcf().number].append(self.data.data_title)
            plt.legend(self.legend_list[plt.gcf().number])
        elif (plot_type == 'grid xy'):
            if (self.data.data.ndim != 3):
                self.add_message("'grid xy' plot is applicable only for a 2D channel matrix.")  
                return
            if (not self.spectrplot_options_autoscale):
                options['Y range'] = plotrange
            try:
                plot_id = psdata.plot(plot_type=plot_type,axes=['Row','Column','Frequency'],plot_id=self.act_plotID,
                                      options=options
                                      )
            except ValueError as e:
                self.add_message("Error: {:s}".format(str(e)))
                return                
        elif (plot_type == 'image'):
            if (self.data.data.ndim != 3):
                self.add_message("'image' plot is applicable only for a 2D channel matrix.")  
                return
            if (not self.spectrplot_options_autoscale):
                options['Z range'] = plotrange
            try:
                plot_id = psdata.plot(plot_type=plot_type,
                                      summing={'Frequency':'Mean'},axes=['Row','Column'],plot_id=self.act_plotID,
                                      options=options
                                      )
            except (ValueError,TypeError) as e:
                self.add_message("Error: {:s}".format(str(e)))
                return                
        elif (plot_type == 'anim-image'):
            if (self.data.data.ndim != 3):
                self.add_message("'anim-image' plot is applicable only for a 2D channel matrix.")  
                return
            if (not self.spectrplot_options_autoscale):
                options['Z range'] = plotrange
            options['Wait'] = 0.01
#            try:
            plot_id = psdata.plot(plot_type=plot_type,
                                  axes=['Row','Column','Frequency'],plot_id=self.act_plotID,
                                  options=options
                                  )
            # except (ValueError,TypeError) as e:
            #     self.add_message("Error: {:s}".format(str(e)))
            #     return                
        else:
            self.add_message("'{:s}' plot not implemented yet.".format(plot_type)) 
            return
        plt.show()
        plt.pause(0.05)
        self.plotID_list[plt.gcf().number] = flap.get_plot_id()
        self.act_plotID = flap.get_plot_id()
        self.add_message("Plot done for {:s}.".format(self.data.data_title))  
    
    def getdata(self):
        """
        Callback function for get data.

        Returns
        -------
        None.

        """
        if (len(self.var_shotID.get() )== 0):
            self.add_message("No Measurement ID (directory name) is set.")
            return
        try:
            t_start = float(self.var_start_time.get())
        except ValueError:
            t_start = None
        try:
            t_end = float(self.var_end_time.get())
        except ValueError:
            t_end = None    
        if ((t_start is not None) and (t_end is not None)):
            coord = {"Time":[t_start,t_end]}
        else:
            coord = None
        try:            
            self.data = flap.get_data('APDCAM',
                                      name=self.var_signals.get(),
                                      coordinates=coord,
                                      options={'Datapath':self.var_shotID.get(),
                                               'Camera type':self.camera_type,
                                               'Camera version':self.camera_version
                                               }
                                      )
            self.add_message("Data '{:s}' read from '{:s}'.".format(self.var_signals.get(),self.var_shotID.get()))   
        except Exception as e:
            self.add_message("Error reading data: {:s}".format(str(e)))    

    def plot_gui_exit(self):
        root.destroy()
        
    def add_message(self,txt):
        """
        Function to add a message to the message area.

        Parameters
        ----------
        txt : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        self.message_widg.insert(tk.END,"\n"+txt)
        self.message_widg.see(tk.END)
        
def plt_loop():
    global root
    plt.pause(0.05)
    root.after(150,plt_loop)
    root.mainloop()
               
def plot_gui():  
     
    global root
    root = tk.Tk()
    print("Creating flap_apdcam plot GUI")
    pgui = APDCAM_Plot_class(root=root)
    GUI_frame_widg = tk.Frame(root)
    GUI_frame_widg.grid()
    GUI_exit_widg = tk.Button(GUI_frame_widg,text='EXIT',command=pgui.plot_gui_exit)
    GUI_exit_widg.grid(row=0,column=0,sticky='e')
    w = tk.Frame(GUI_frame_widg)
    w.grid(row=1,column=0)
    root.title(string='flap_apdcam plot graphical interface')
    thisdir = os.path.dirname(os.path.realpath(__file__))
    if (os.name == 'nt'):
        root.iconbitmap(os.path.join(thisdir,'flap_apdcam_icon.ico'))
    else:
        root.iconphoto(True, tk.PhotoImage(os.path.join(thisdir,'flap_apdcam_icon.gif')))    
    pgui.create_widgets(parent=w)
    # GUI_frame_widg.after(0,plt_loop)
    # GUI_frame_widg.mainloop()
    root.after(150,plt_loop)
    root.mainloop()