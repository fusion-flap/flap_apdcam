# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 22:23:47 2022

GUI for plotting APDCAM data

@author: Zoletnik
"""
import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import *

import matplotlib.pyplot as plt
import flap
import flap
import flap_apdcam
      
class APDCAM_Plot_class:
    
    def __init__(self):
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
        self.camera_type_list, self.camera_version_list_list = flap_apdcam.apdcam_types_versions()
        self.camera_version_list = None
        

    def create_widgets(self,parent,config_file=None,camera_type=None,camera_version=None):
        
        plot_background = 'lavender'
        self.camera_type = camera_type
        self.camera_version = camera_version
        if (config_file is not None):
            flap.config.read(file_name=config_file)
        self.config_file = config_file
        self.plotControl_widg = tk.LabelFrame(parent,bd=2, padx=2, pady=2,relief=tk.GROOVE,text='Plot control',bg=plot_background)
        self.plotControl_widg.grid(row=0,column=0)
        
        row0 = 0
        if ((camera_type is None) or (camera_version is None)):
            camera_settings_frame = tk.LabelFrame(self.plotControl_widg,bd=4, padx=2, pady=2,relief=tk.GROOVE,text='Camera selection',bg=plot_background)
            camera_settings_frame.grid(row=0,column=0)
            row0 = 1
            if (camera_type is None):
                w = tk.Label(camera_settings_frame,text='Camera type:',bg=plot_background).grid(row=0,column=0,sticky='e')
                self.camera_select_widg = tk.OptionMenu(camera_settings_frame,self.var_camera_type,*tuple(self.camera_type_list),command=self.camera_type_select)
                self.camera_select_widg.grid(row=0,column=1,sticky='w')
            if (camera_version is None):
                w = tk.Label(camera_settings_frame,text='Camera version:',bg=plot_background).grid(row=1,column=2,sticky='e')
                self.camera_version_select_widg = tk.OptionMenu(camera_settings_frame,self.var_camera_version,("n.a"),command=self.camera_version_select)
                self.camera_version_select_widg.grid(row=0,column=3,sticky='w')
                
                
        general_settings_frame = tk.Frame(self.plotControl_widg,bg=plot_background)
        general_settings_frame.grid(row=row0,column=0)
        w = tk.Label(general_settings_frame,text='Measurement ID:',bg=plot_background).grid(row=0,column=0,sticky='e')
        self.shotID_widg = tk.Entry(general_settings_frame,width=10,textvariable=self.var_shotID,bg=plot_background)
        self.shotID_widg.grid(row=0,column=1,sticky='w')
        w = tk.Label(general_settings_frame,text='Signals:',bg=plot_background).grid(row=0,column=2,sticky='e')
        self.signals_widg = tk.Entry(general_settings_frame,width=10,textvariable=self.var_signals,bg=plot_background)
        self.signals_widg.grid(row=0,column=3,sticky='w')
        time_frame = tk.Frame(general_settings_frame,bg=plot_background)
        time_frame.grid(row=1,column=0,columnspan=4)
        w = tk.Label(time_frame,text='Timerange[s]:',bg=plot_background).grid(row=0,column=0,sticky='e')
        self.start_time_widg = tk.Entry(time_frame,width=10,textvariable=self.var_start_time,bg=plot_background)
        self.start_time_widg.grid(row=0,column=1,sticky='e')
        w = tk.Label(time_frame,text='-',bg=plot_background).grid(row=0,column=2,sticky='e')
        self.end_time_widg = tk.Entry(time_frame,width=10,textvariable=self.var_end_time,bg=plot_background)
        self.end_time_widg.grid(row=0,column=3,sticky='w')
        self.getdata_widg = tk.Button(general_settings_frame,command=self.getdata,text='GET DATA',bg=plot_background)
        self.getdata_widg .grid(row=2,column=0,columnspan=2)
        w = tk.Label(general_settings_frame,text='Figure:',bg=plot_background).grid(row=2,column=2,sticky='e')
        self.figure_select_widg = tk.OptionMenu(general_settings_frame,self.var_figure,*tuple(self.figure_list),command=self.figure_select)
        self.figure_select_widg.grid(row=2,column=3,sticky='w')
        self.var_figure.set(self.figure_list[0])
        self.message_widg = tk.Text(general_settings_frame,font=('Times','10'),height=2,width=80,bg=plot_background)
        self.message_widg.grid(row=3,column=0,columnspan=4)    
        
        self.rawplot_widg = tk.LabelFrame(self.plotControl_widg,bd=4, padx=2, pady=2,relief=tk.GROOVE,text='Raw data plot',bg=plot_background)
        self.rawplot_widg.grid(row=row0 + 1,column=0,columnspan=4)
        self.rawplot_button_widg = tk.Button(self.rawplot_widg,command=self.rawplot,text='PLOT',bg=plot_background)
        self.rawplot_button_widg.grid(row=0,column=0)
        w = tk.Label(self.rawplot_widg,text='Plot type:',bg=plot_background).grid(row=0,column=1,sticky='e')
        self.plot_type_select_widg = tk.OptionMenu(self.rawplot_widg,self.plot_type,*tuple(self.plot_type_list),command=self.plot_type_select)
#        self.plot_type_select_widg["menu"].config(bg=plot_background,fg=plot_background)
        self.plot_type_select_widg.grid(row=0,column=2,sticky='w')
   
    def camera_type_select(self,event):
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
        print("camera_type:{:s}, camera_version:{:s}".format(self.camera_type,str(self.camera_version)))
        
    def camera_version_select(self,event):
        if (self.camera_type is None):
            return
        self.camera_version = int(self.var_camera_version.get())
        print("camera_type:{:s}, camera_version:{:s}".format(self.camera_type,str(self.camera_version)))

        
    def figure_select(self,event):
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
                plt.plotID_list[int(self.var_figure.get())] = None
                self.legend_list[int(self.var_figure.get())] = []
        #     figure_list_int = []
        #     for i in range(1,len(self.figure_list)):
        #         figure_list_int.append(int(self.figure_list[i]))
        #     temp = [(v,i) for i,v in enumerate(figure_list_int)]
        #     temp.sort
        #     ind,figure_list_ind = zip(*temp)
        #     plotID_tmp = self.plotID_list[1:]
        #     self.figure_list = [self.figure_list[0]]
        #     self.plotID_list = [self.plotID_list[0]]
        #     for i in figure_list_int:
        #         self.figure_list.append(str(i))
        #         self.plotID_list.append([plotID_tmp[ind[i]]])
        menu = self.figure_select_widg['menu']
        menu.delete("0",tk.END)
        for i,item in enumerate(self.figure_list):
            menu.add_command(label=item,command=tk._setit(self.var_figure,item,self.figure_select))
        self.var_figure.set(self.figure_list[plt.gcf().number])
        self.act_plotID = self.plotID_list[plt.gcf().number]
            
    def plot_type_select(self,event):
        pass          
            
    def rawplot(self):
        if (self.data is None):
            self.add_message("Cannot plot, load data first.")  
            return
        self.figure_select(None)
        plot_type = self.plot_type.get()
        if (plot_type == 'xy'):
            if (self.data.data.ndim != 1):
                self.add_message("'xy plot' is applicable only for a single channel like APD-2-3.")  
                return
            self.data.plot(plot_type=self.plot_type.get(),axes=['Time'],plot_id=self.act_plotID)
            self.legend_list[plt.gcf().number].append(self.data.data_title)
            plt.legend(self.legend_list[plt.gcf().number])
            plt.show()
            plt.pause(0.05)
            self.plotID_list[plt.gcf().number] = flap.get_plot_id() 
            self.add_message("Plot done for {:s}.".format(self.data.data_title))  
        elif (self.plot_type.get() == 'grid xy'):
            if (self.data.ndim != 3):
                self.add_message("'grid xy' plot is applicable only for a 2D channel matrix.")  
                return
            self.data.plot(plot_type=self.plot_type.get(),axes=['Row','Column','Time'])
        else:
            self.add_message("'{:s}' plot not implemented yet.".format(plot_type))  
            
    def getdata(self):
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
        except (ValueError,IOError) as e:
            self.add_message("Error reading data: {:s}".format(str(e)))    

    def plot_gui_exit(self):
        root.destroy()
        
    def add_message(self,txt):
        self.message_widg.insert(tk.END,"\n"+txt)
        self.message_widg.see(tk.END)
        
               
def plot_gui():  
    flap_apdcam.register()
     
    global root
    root = tk.Tk()
    print("Creating plot GUI")
    pgui = APDCAM_Plot_class()
    GUI_frame_widg = tk.Frame(root)
    GUI_frame_widg.grid()
    GUI_exit_widg = tk.Button(GUI_frame_widg,text='EXIT',command=pgui.plot_gui_exit)
    GUI_exit_widg.grid(row=0,column=0,sticky='e')
    w = tk.Frame(GUI_frame_widg)
    w.grid(row=1,column=0)
    pgui.create_widgets(parent=w)
    GUI_frame_widg.mainloop()