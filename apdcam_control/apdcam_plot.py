# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 22:23:47 2022

GUI for plotting APDCAM data

@author: Zoletnik
"""
import tkinter as tk
from tkinter import messagebox

import matplotlib.pyplot as plt
import flap

      
class APDCAM_Plot_class:
    
    def __init__(self):
        self.var_shotID = tk.StringVar()
        self.var_shotID.set(value="")
        self.var_figure = tk.StringVar()
        self.figure_list = ['New figure']
        self.var_signals = tk.StringVar()
        self.var_signals.set('APD-*')
        plt.close('all')
        self.figsize=(20,15)
        self.var_end_time = tk.StringVar()
        self.var_end_time.set(value="")      
        self.var_start_time = tk.StringVar()
        self.var_end_time.set(value="")
        self.plot_type_list = ['grid xy','image','anim-image']
        self.plot_type = tk.StringVar()
        self.data = None
        

    def create_widgets(self,parent,config_file=None,camera_type=None,camera_version=None):
        self.camera_type = camera_type
        self.camera_version = camera_version
        if (config_file is not None):
            flap.config.read(file_name=config_file)
        self.config_file = config_file
        self.plotControl_widg = tk.LabelFrame(parent,bd=2, padx=2, pady=2,relief=tk.GROOVE,text='Plot control')
        self.plotControl_widg.grid(row=0,column=0)
        
        general_settings_frame = tk.Frame(self.plotControl_widg)
        general_settings_frame.grid()
        w = tk.Label(general_settings_frame,text='Measurement ID:').grid(row=0,column=0,sticky='e')
        self.shotID_widg = tk.Entry(general_settings_frame,width=10,textvariable=self.var_shotID)
        self.shotID_widg.grid(row=0,column=1,sticky='w')
        w = tk.Label(general_settings_frame,text='Signals:').grid(row=0,column=2,sticky='e')
        self.signals_widg = tk.Entry(general_settings_frame,width=10,textvariable=self.var_signals)
        self.signals_widg.grid(row=0,column=3,sticky='w')
        time_frame = tk.Frame(general_settings_frame)
        time_frame.grid(row=1,column=0,columnspan=4)
        w = tk.Label(time_frame,text='Timerange[s]:').grid(row=0,column=0,sticky='e')
        self.start_time_widg = tk.Entry(time_frame,width=10,textvariable=self.var_start_time)
        self.start_time_widg.grid(row=0,column=1,sticky='e')
        w = tk.Label(time_frame,text='-').grid(row=0,column=2,sticky='e')
        self.end_time_widg = tk.Entry(time_frame,width=10,textvariable=self.var_end_time)
        self.end_time_widg.grid(row=0,column=3,sticky='w')
        self.getdata_widg = tk.Button(general_settings_frame,command=self.getdata,text='GET DATA')
        self.getdata_widg .grid(row=2,column=0,columnspan=2)
        w = tk.Label(general_settings_frame,text='Figure:').grid(row=2,column=2,sticky='e')
        self.figure_select_widg = tk.OptionMenu(general_settings_frame,self.var_figure,*tuple(self.figure_list),command=self.figure_select)
        self.figure_select_widg.grid(row=2,column=3,sticky='w')
        self.message_widg = tk.Text(general_settings_frame,font=('Times','10'),height=2,width=80)
        self.message_widg.grid(row=3,column=0,columnspan=4)    
        
        self.rawplot_widg = tk.LabelFrame(self.plotControl_widg,bd=4, padx=2, pady=2,relief=tk.GROOVE,text='Raw data plot')
        self.rawplot_widg.grid(row=1,column=0)
        self.rawplot_button_widg = tk.Button(self.rawplot_widg,command=self.rawplot,text='PLOT')
        self.rawplot_button_widg.grid(row=0,column=0)
        w = tk.Label(self.rawplot_widg,text='Plot type:').grid(row=0,column=1,sticky='e')
        self.plot_type_select_widg = tk.OptionMenu(self.rawplot_widg,self.plot_type,*tuple(self.plot_type_list),command=self.plot_type_select)
        self.plot_type_select_widg.grid(row=0,column=2,sticky='w')
        
    def figure_select(self,event):
        if (self.var_figure.get() == self.figure_list[0]):
            figno = plt.figure(figsize=self.figsize)
            self.figure_list.append(str(plt.gcf().number))
        else:
            try:
                plt.get_fignums().index(int(self.var_figure.get()))
                plt.figure(int(self.var_figure.get()))
            except ValueError:
                plt.figure(int(self.var_figure.get()),figsize=self.figsize)
            figure_list_int = []
            for i in range(1,len(self.figure_list)):
                figure_list_int.append(int(self.figure_list[i]))
            figure_list_int.sort()
            self.figure_list = [self.figure_list[0]]
            for i in figure_list_int:
                self.figure_list.append(str(i))
        menu = self.figure_select_widg['menu']
        menu.delete("0",tk.END)
        for i,item in enumerate(self.figure_list):
            menu.add_command(label=item,command=tk._setit(self.var_figure,item,self.figure_select))
            
    def plot_type_select(self,event):
        pass          
            
    def rawplot(self):
        if (self.data is None):
            self.add_message("Cannot plot, load data first.")    
        print("Plotting.")
        
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
            self.add_message("Data read.")   
        except (ValueError,IOError) as e:
            self.add_message("Error reading data: {:s}".format(str(e)))    

    def plot_gui_exit(self):
        root.destroy()
        
    def add_message(self,txt):
        self.message_widg.insert(tk.END,"\n"+txt)
        self.message_widg.see(tk.END)
        
               
def plot_gui():       
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