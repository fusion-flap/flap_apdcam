# -*- coding: utf-8 -*-
"""
This is the graphical user interface for the Alkali BES diagnostic on
Wendelstein 7-X
 Author: S. Zoletnik  April 2019, based on W7-X ABES GUI
      
 """
 
 
import tkinter as tk
from tkinter import messagebox
import threading
import datetime
import time
import pathlib
import configparser
import subprocess

import matplotlib.pyplot as plt


#from .APDCAM10G_control import *

#from .read_config
        
class APDCAM_GUI_config_class:
    CLK_INTERNAL = 0
    CLK_EXTERNAL = 1
    def __init__(self):
        self.configFile = "APDCAM_GUI.cfg"
        self.clockSource = APDCAM_GUI_config_class.CLK_INTERNAL
        self.triggerTime = 0.0
        self.datapath = "data"
        self.APDCAMStartTime = 0

class APDCAM_GUI_status_class:
    """ This contains various information about the system and shared
        by all GUI blocks.
    """
    def __init__(self) :
        self.APDCAM_on = False
        self.APDCAM_connected = False
        self.Update_APDCAM  = False  # If 1 update widgets from hardware
        self.APDCAM_reg = None
        self.APDCAM_data = None

        self.CMOS_on = False
        self.CMOS_connected = False
        self.Update_CMOS = False

        self.Beam_connected = False
        self.Update_beam = False

        # This is set ot True if stop measurement is requested
        self.stopMeasurement = False 
        # This indicates that measurement is running
        self.measurementRunning = False
        
        self.GUI = None # this is the instance of the shot_Control_class. 
                        # Can be used e.g. as self.GUI.add_message("text")
        self.GUI_top = None # This is the instance of the APDCAM_GUI class
        self.config = APDCAM_GUI_config_class()

class startup_message_class :
    def __init__(self):
        self.messages = []
    
    def collect_startup_messages(self,message):
        self.messages.append(message)
               
class APDCAM_GUI_class(tk.Frame):
    def __init__(self, master=None,show_data_func = None):
        super().__init__(master)
        # This is the global status block
        self.state = APDCAM_GUI_status_class()
        
        self.state.GUI_top = self
        self.state.root_widg = master
        
         
        # Instantiating the sub-GUIs 
        self.GUI_shotControl_widg = \
            GUI_shotControl_class(GUI_status=self.state,show_data_func=show_data_func)
        self.GUI_APDCAM_widg = APDCAM10G_GUI_class(GUI_status=self.state)

        # Creating a list of the sub-GUIs. 

        self.widget_list = [self.GUI_shotControl_widg, \
                            self.GUI_APDCAM_widg]

        # This will collect any error message during read_config
        # After the widgets are created self.state.GUI.add_message will be redirected
        # to GUI_shotControl_class.add_message_func() and the collected messages sent to it.
        sm = startup_message_class()
        self.state.GUI.add_message = sm.collect_startup_messages
        self.read_config()
        
        
        # Showing the top-level widget
        self.grid()
        
        self.create_widgets()
        
        
        for i in range(len(sm.messages)):
            self.state.GUI.add_message(sm.messages[i])
            
        self.set_defaults()
        self.start()

        
    def create_widgets(self):
        
        GUI_frame_widg = tk.Frame(self)
        GUI_frame_widg.grid()

        col1 = tk.Frame(GUI_frame_widg)
        col1.grid(row=1,column=1)
        shotControlFrame = tk.Frame(col1)
        shotControlFrame.grid(row=1,column=1)       
        self.GUI_shotControl_widg.create_widgets(shotControlFrame)
            
        APDCAMControlFrame = tk.Frame(col1)
        APDCAMControlFrame.grid(row=3,column=1)   
        self.GUI_APDCAM_widg.create_widgets(APDCAMControlFrame) 
            
    def config_get(self,file,section,key) :
        """ Reads an element from a configuration file
        The file format is 
        [Section]
        key = value
        # comment
        """
        config = configparser.ConfigParser()
        try:
            config.read(file)
        except :
            err = "Error reading file "+file
            return err, None
        try:
            value = config[section][key]
        except:
            err = "Error reading key "+key+" from section "+section+" from file "+file
            return err,None
        return "", value
        
    def readConfigElement(self,section,element,default,datatype):
        """ Reads an element from the config file. If not found or conversion
            error occurs sends an error message through add_message().
            Returns the value read or the default.
            This is a helper for the set_defaults method.
        """
        
        err,txt = self.config_get(self.state.config.configFile,section,element)
        if (err == ""):
            try:
                if (datatype == 'float'):
                    val = float(txt)
                elif (datatype == 'int'):
                    val = int(txt)
                elif (datatype == 'string'):
                    val = txt
            except:
                err = "Invalid value ("+txt+") for "+element+" entry in section "+section+" in config file:"+self.state.config.configFile 
        else :
            err = "Error reading "+element+" entry in section "+section+" in config file:"+self.state.config.configFile+\
                    "\n Using \""+str(default)+"\" as default."
        if (err != ""):
            val = default
            self.state.GUI.add_message(err)
        return val
       
        
    def read_config(self):
        self.state.config.datapath = self.readConfigElement("General","Datapath","data","string")
        self.state.config.camera_type = self.readConfigElement("General","CameraType","","string")
        self.state.config.camera_version = self.readConfigElement("General","CameraVersion","","string")
        self.state.config.APDCAMStartTime = self.readConfigElement("Trigger","APDCAMStartTime",0,"float")       
        self.state.config.triggerTime = self.readConfigElement("Trigger","TriggerTime",0,"float")
        txt = self.readConfigElement("Trigger","ClockSource","INTERNAL","string")
        if (txt.lower() == "internal"):
                self.state.config.clockSource =   APDCAM_GUI_config_class.CLK_INTERNAL
        elif (txt.lower() == "external"):
                self.state.config.clockSource =   APDCAM_GUI_config_class.CLK_EXTERNAL
        else:
            self.state.GUI.add_message("Invalid ClockSource value in config file. Using INTERNAL.")
            self.state.config.clockSource =   APDCAM_GUI_config_class.CLK_INTERNAL
                  
        self.state.config.channel_masks = [0xffffffff,0xffffffff]        
                        
    def set_defaults(self):              
        for w in self.widget_list :
            w.set_defaults()
       
    def start(self):
        for w in self.widget_list :
            w.start()

    def stop(self):
        for w in self.widget_list :
            w.stop()
        time.sleep(0.5)    
    
class GUI_shotControl_class :
    def __init__(self, GUI_status=None,show_data_func=None):
        self.GUI_status = GUI_status
        self.var_shotID= tk.StringVar()
        self.var_shot_mode= tk.StringVar()
        self.var_meas_start = tk.StringVar()
        self.var_meas_length = tk.StringVar()
        self.GUI_status.GUI = self
        self.show_data_func = show_data_func
        
    def create_widgets(self,parent):
        self.frame_widg = tk.Frame(parent)
        self.frame_widg.grid(row=1,column=1)
        self.frame_widg["bd"] = 2
        self.frame_widg["padx"] = 2
        self.frame_widg["pady"] = 2
        
        w = tk.Frame(self.frame_widg)
        w.grid(row=1,column=1)
        self.start_button_widg = tk.Button(w, text="START measurement")
        self.start_button_widg["font"] = ('Helvetica', '12')
        self.start_button_widg["width"] = 20
        self.start_button_widg["height"] = 1
        self.start_button_widg["bg"] = 'green'
        self.start_button_widg["command"] = self.startExp
        self.start_button_widg.grid(row=1,column=1)
        
        self.stop_button_widg = tk.Button(w, text="STOP measurement")
        self.stop_button_widg["bg"] = 'red'
        self.stop_button_widg["font"] = ('Helvetica', '12')
        self.stop_button_widg["width"] = 20
        self.stop_button_widg["height"] = 1
        self.stop_button_widg["command"] = self.stopExp
        self.stop_button_widg.grid(row=1,column=2)

#        w_stat = tk.Frame(self.frame_widg)
#        w_stat.grid(row=1,column=2)
#        self.prep_widg = tk.Button(w_stat, text=" ")
#        self.prep_widg["font"] = ('Helvetica', '8')
#        self.prep_widg["width"] = 15
#        self.prep_widg["height"] = 1
#        self.prep_widg["bg"] = 'white'
#        self.prep_widg.grid(row=1,column=1)
#
#        self.meas_widg = tk.Button(w_stat, text="measure")
#        self.meas_widg["font"] = ('Helvetica', '8')
#        self.meas_widg["width"] = 15
#        self.meas_widg["height"] = 1
#        self.meas_widg["bg"] = 'white'
#        self.meas_widg.grid(row=1,column=2)
# 
#        self.save_widg = tk.Button(w_stat, text="save data")
#        self.save_widg["font"] = ('Helvetica', '8')
#        self.save_widg["width"] = 15
#        self.save_widg["height"] = 1
#        self.save_widg["bg"] = 'white'
#        self.save_widg.grid(row=1,column=3)
        
        self.exit_button_widg = tk.Button(self.frame_widg, text="EXIT")
        self.exit_button_widg["font"] = ('Helvetica', '16')
        self.exit_button_widg["command"] = self.exitGUI
        self.exit_button_widg.grid(row=1,column=3)
        
        self.message_widg = tk.Text(self.frame_widg,font=('Times','10'), \
                                    height=6,width=80)
        self.message_widg.grid(row=2,column=1,columnspan=3)
        
        shotSettingsFrame = tk.Frame(self.frame_widg , bd=2, padx=2, pady=2)
        shotSettingsFrame.grid(row=3,column=1,columnspan=3)
        w = tk.Label(shotSettingsFrame,text='Test ID:').grid(row=1,column=1)
        self.shotID_widg = tk.Entry(shotSettingsFrame,width=15,textvariable=self.var_shotID)
        self.shotID_widg.grid(row=1,column=2)
        optionList = ('Test','Test w. trigger')
        self.var_shot_mode.set(optionList[0])
        self.shot_mode_widg = tk.OptionMenu(shotSettingsFrame,self.var_shot_mode,*optionList)
        self.shot_mode_widg.grid(row=1,column=3)                                    
        self.shot_mode_widg["width"] = 17
        
        w = tk.Label(shotSettingsFrame,text='Measurement length[s]:').grid(row=2,column=3)
        self.meas_length_widg = tk.Entry(shotSettingsFrame,width=15,textvariable=self.var_meas_length)
        self.meas_length_widg.grid(row=2,column=4)
        
        self.add_message = self.add_message_func
        
    def set_defaults(self) :
        self.var_meas_length.set("1.0")
    
    def start(self):
        pass
    
    def stop(self):
        pass
    
    def add_message_func(self,txt,log=False):
        self.message_widg.insert(tk.END,txt+"\n")
        self.message_widg.see(tk.END)
        
        
    def runMeasurement(self) :
        """ This is a separate thread which runs the measurement sequence
        It will abort if self.GUI_status.stopMeasurement is True
        """
  
        
        # The APDCAM control class instance
        apd = self.GUI_status.APDCAM_reg
    
        shotmode = self.var_shot_mode.get()
        test_shot_trigger = False
        if (shotmode == 'Test w. trigger'):
            shotmode = 'Test'
            test_shot_trigger = True
            
        meas_start_time = float(0)
            
        txt = self.var_meas_length.get()
        try:
            meas_length = float(txt)
        except:
            v= tk.messagebox.showerror("Error", "Invalid measurement length.")
            self.add_message("Aborted measurement.") 
            self.GUI_status.measurementRunning = False
            return                    
       
        if (not self.GUI_status.APDCAM_connected):
            v= tk.messagebox.showerror("Error", "Cannot run a measurement without APDCAM")
            self.add_message("Aborted measurement.") 
            self.GUI_status.measurementRunning = False
            return                    
                            
        today = datetime.datetime.now()
        try:
            # Get the last test shot date and number
            f = open("APDCAM_GUI_testshot_counter.dat","rt")
            lastyear = int(f.readline())
            lastmonth = int(f.readline())
            lastday = int(f.readline())
            lastshot = int(f.readline())
            f.close()
            if (lastyear != today.year) or (lastmonth != today.month) or (lastday != today.day):
                # Starting new counting
                act_shot = 1
                act_year = today.year
                act_month = today.month
                act_day = today.day
            else:
                # There was a test shot today already
                act_shot = lastshot+1
                act_year = today.year
                act_month = today.month
                act_day = today.day                  
        except:
            # There is no information on the last test shot
            act_shot = 1
            act_year = today.year
            act_month = today.month
            act_day = today.day
        shotID = "T"+str(act_year)+"{:=02d}".format(act_month)+"{:=02d}".format(act_day)+"."+"{:=03d}".format(act_shot)    
        
        # Here we have a shotID
        
        #Noting the current time
        shot_start_time = datetime.datetime.now()

        # Checking whether this shot already exists        
        self.var_shotID.set(shotID)
        shot_path = self.GUI_status.config.datapath+'/'+shotID
        p = pathlib.Path(shot_path)
        if (p.exists()):
            v= tk.messagebox.askokcancel("Warning", "Program (shot) directory\n"+shot_path+"\nexists\nOverwrite?", default=tk.messagebox.OK)
            if (v == False):
                self.add_message("Aborted measurement.") 
                self.GUI_status.measurementRunning = False
                return
                        
        # Looping to start actions at different times.
        # This loop will stop on abort, error or measurement finished
        APDCAM_started = False
        APDCAM_finished = False # Will be True when APCAM finished and data stored
        
        APDCAM_start_time = 0
        shot_pretrig_time = 0

        while (not self.GUI_status.stopMeasurement) :
            act_time = datetime.datetime.now()
            dt = act_time - shot_start_time
            time_to_shot = shot_pretrig_time - dt.seconds
                
            if ((self.GUI_status.APDCAM_connected) \
                    and not APDCAM_started \
                    and (time_to_shot <= APDCAM_start_time)):
                       
                err,APD_settings = self.GUI_status.GUI_top.GUI_APDCAM_widg.read_settings()
                numberOfSamples = round(meas_length*APD_settings.samplerate*1E6)
                chmask = copy.deepcopy(self.GUI_status.config.channel_masks)
                chmask.append(0xffffffff)
                chmask.append(0xffffffff)
                
                if (test_shot_trigger):
                    externalTriggerPolarity = 0
                else:    
                    externalTriggerPolarity = None
                    
                self.add_message("Starting APDCAM.")
                self.GUI_status.Update_APDCAM = False
                time.sleep(0.5)
                err, warning = apd.measure(numberOfSamples=numberOfSamples,\
                                  channelMasks=chmask,\
                                  sampleDiv=APD_settings.sampleDiv,\
                                  datapath="data",\
                                  bits=14,\
                                  waitForResult=False,\
                                  externalTriggerPolarity=externalTriggerPolarity,\
                                  triggerDelay=(meas_start_time-self.GUI_status.config.triggerTime)*1e6)
                if (err != ""):
                    err = "Error starting APDCAM: "+err
                    self.add_message(err) 
                    self.GUI_status.measurementRunning = False
                    break
                self.add_message("APDCAM started.")
                if (externalTriggerPolarity is not None):
                    self.add_message("Waiting for trigger...")
                time.sleep(1)
                APDCAM_started = True
                        
            # Stopping waiting loop if measurement time has passed
            if ((externalTriggerPolarity is None) and (-time_to_shot > meas_start_time+meas_length+2)) :
                self.add_message("Measurement time is over.")
                break

            err,stat,warning = apd.measurementStatus()
            if (err != ""):
                err = "Error reading APDCAM status: "+err
                self.add_message(err) 
                break
            if (stat == "Finished"):
                break
            
            time.sleep(0.1) 
      
        # end of waiting loop

        
        # Waiting for APDCAM to stop
        # APDCAM might need some time to write data
        APDCAM_save_time = (APD_settings.samplerate*meas_length)*1 + 5  
        w = False
        while (APDCAM_started):  
            err,stat,warning = apd.measurementStatus()
            if (err != ""):
                err = "Error reading APDCAM status: "+err
                self.add_message(err) 
                break
            if (stat == "Finished"):
                APDCAM_finished = True
                self.add_message("APDCAM finished measurement.")
                err = apd.writeConfigFile()
                if (err != ""):
                   self.add_message("Error writing config file: "+err)  
                break
            if (not w) :
                self.add_message("Waiting for APDCAM to finish.")
                w = True
            act_time = datetime.datetime.now()
            dt = act_time - shot_start_time
            time_after_shot = dt.seconds - shot_pretrig_time 
            if (time_after_shot > meas_start_time + meas_length + APDCAM_save_time):
                self.add_message("APDCAM did not stop. Killing it.")
                apd.abortMeasurement()
#                    cmd = "killall APDTest"
#                    d = subprocess.run([cmd],check=False,shell=True)
                break
            if (self.GUI_status.stopMeasurement) :
                break
            time.sleep(1)
        
        self.GUI_status.Update_APDCAM = True
                
        # Here all data are on the disk or error happened
        # moving data to datapath
        shotdir = self.GUI_status.config.datapath+"/"+shotID
        self.add_message("Copying data to "+shotdir)
        cmd = "mkdir "+shotdir+" ; cp data/Channel*.dat data/APDCAM_config.xml data/apd_python_meas.cmd "\
            +"data/APDTest.out "+shotdir+"/"
        d=subprocess.run([cmd],check=False,shell=True,stdout=subprocess.PIPE)
        self.add_message("Data copy finished.")

        self.GUI_status.measurementRunning = False
        self.add_message("Shot "+shotID+" finished.")
                     
        try:
            f = open("APDCAM_GUI_testshot_counter.dat","wt")
            f.writelines(str(act_year)+"\n"+str(act_month)+"\n"+str(act_day)+"\n"+str(act_shot))
            f.close()
        except:
           self.add_message("Warning: Could not write last test shot number into file.") 

        if (self.show_data_func is not None):
            f = open("diag.py","wt")
            f.write("from "+self.show_data_func+" import *\n")
            f.write(self.show_data_func+"(datapath='"+shotdir+"')\n")
            f.write("input('Press Enter to continue...')\n")
            f.close()
            cmd = "xterm -e python diag.py &"
            d=subprocess.run([cmd],check=False,shell=True) 
        else:
            pass
 
    # End of run_measurement
            
    def startExp(self) :
        """ This is called when the start button is pressed.
        """
        if (self.GUI_status.measurementRunning):
            self.add_message("Measurement is already runnig.")
            return
        self.GUI_status.measurementRunning = True
        self.GUI_status.stopMeasurement = False
        self.testThread = threading.Thread(target=self.runMeasurement)
        self.testThread.start()
        
    def stopExp(self) :
        print("Stop experiment pressed") 
        self.GUI_status.stopMeasurement = True
        
        
    
    def exitGUI(self) :
        print("Exit pressed")
        self.GUI_status.GUI_top.stop()
        self.GUI_status.root_widg.destroy()

class APDCAM_settings:
    def __init__(self):
        self.samplerate = 0  # MHz
        self.sampleDiv = 0 # Calculated from samplerate
    
class APDCAM10G_GUI_class:
    OffColor = "#FCC"
    OnColor = "#CFC"
    TryColor = "yellow"
    DETECTOR_TEMP_SENSOR = 5 # 1...
    BASE_TEMP_SENSOR = 11
    AMP_TEMP_SENSOR = 6
    POWER_TEMP_SENSOR = 16
    
    def __init__(self,GUI_status=None):
        self.GUI_status = GUI_status
        self.GUI_status.APDCAM_reg = None
        self.updateThread = None
        self.stopThreadSignal = 0
        self.GUI_status.Update_APDCAM = False
        self.GUI_status.APDCAM_connected = False
        self.var_HV1_set = tk.StringVar()
        self.var_HV2_set = tk.StringVar()
        self.var_HV3_set = tk.StringVar()
        self.var_HV4_set = tk.StringVar()
        self.var_HV1_act = tk.StringVar()
        self.var_HV2_act = tk.StringVar()
        self.var_HV3_act = tk.StringVar()
        self.var_HV4_act = tk.StringVar()
        self.var_detTemp_act = tk.StringVar()
        self.var_detTemp_set = tk.StringVar()
        self.var_baseTemp_act = tk.StringVar()
        self.var_ampTemp_act = tk.StringVar()
        self.var_powerTemp_act = tk.StringVar()
        self.var_CCTemp_act = tk.StringVar()
        self.var_APDCAM_sample = tk.StringVar()
        self.APDCAM_samplerates = []
        self.APDCAM_samplerate_names = []
        
    def create_widgets(self,parent) :
        self.frame_widg = tk.LabelFrame(parent,bd=2,relief=tk.GROOVE,padx=2,pady=2,text="APDCAM")
        self.frame_widg.grid(row=1,column=1)
        
        pwblock = tk.Frame(self.frame_widg)
        pwblock.grid(row=1,column=1)
        self.APDCAM_on_widg = tk.Button(pwblock,text='APDCAM on',\
                                           command=self.APDCAM_on,width=11)         
        self.APDCAM_on_widg.grid(row=1,column=1)
        self.APDCAM_off_widg = tk.Button(pwblock,text='APDCAM off',\
                                           command=self.APDCAM_off,width=11) 
        self.APDCAM_off_widg.grid(row=1,column=2)        
        self.APDCAM_comm_widg = tk.Label(pwblock,text='Not connected',bg=APDCAM10G_GUI_class.OffColor,\
                                        width=14)  
        self.APDCAM_comm_widg.grid(column=3,row=1)
        
        # HV block
        hvblock = tk.LabelFrame(self.frame_widg,text="Detector voltages")
        hvblock.grid(row=2,column=1)
        w = tk.Label(hvblock,text='HV1 set:').grid(row=1,column=1)
        self.HV1_set_widg = tk.Entry(hvblock,width=6,textvariable=self.var_HV1_set)
        self.HV1_set_widg.bind('<Return>',self.hv1_set)
        self.HV1_set_widg.grid(row=1,column=2)
        w = tk.Label(hvblock,text='actual:').grid(row=1,column=3)
        self.HV1_stat_widg = tk.Entry(hvblock,width=6,textvariable=self.var_HV1_act)
        self.HV1_stat_widg.grid(row=1,column=4)
        self.HV1_on_widg = tk.Button(hvblock,text="HV1 on",command=self.hv1_on)
        self.HV1_on_widg.grid(row=1,column=5)
        self.HV1_off_widg = tk.Button(hvblock,text="HV1 off",command=self.hv1_off)
        self.HV1_off_widg.grid(row=1,column=6)
        self.HV_en_widg = tk.Button(hvblock,text="HV Enable",width=10,command=self.hv_enable)
        self.HV_en_widg.grid(row=1,column=7)
        
        w = tk.Label(hvblock,text='HV2 set:').grid(row=2,column=1)
        self.HV2_set_widg = tk.Entry(hvblock,width=6,textvariable=self.var_HV2_set)
        self.HV2_set_widg.bind('<Return>',self.hv2_set)
        self.HV2_set_widg.grid(row=2,column=2)
        w = tk.Label(hvblock,text='actual:').grid(row=2,column=3)
        self.HV2_stat_widg = tk.Entry(hvblock,width=6,textvariable=self.var_HV2_act)
        self.HV2_stat_widg.grid(row=2,column=4)
        self.HV2_on_widg = tk.Button(hvblock,text="HV2 on",command=self.hv2_on)
        self.HV2_on_widg.grid(row=2,column=5)
        self.HV2_off_widg = tk.Button(hvblock,text="HV2 off",command=self.hv2_off)
        self.HV2_off_widg.grid(row=2,column=6)
        self.HV_disable_widg = tk.Button(hvblock,text="HV Disable",width=10,command=self.hv_disable)
        self.HV_disable_widg.grid(row=2,column=7) 
        
        w = tk.Label(hvblock,text='HV3 set:').grid(row=3,column=1)
        self.HV3_set_widg = tk.Entry(hvblock,width=6,textvariable=self.var_HV3_set)
        self.HV3_set_widg.bind('<Return>',self.hv3_set)
        self.HV3_set_widg.grid(row=3,column=2)
        w = tk.Label(hvblock,text='actual:').grid(row=3,column=3)
        self.HV3_stat_widg = tk.Entry(hvblock,width=6,textvariable=self.var_HV3_act)
        self.HV3_stat_widg.grid(row=3,column=4)
        self.HV3_on_widg = tk.Button(hvblock,text="HV3 on",command=self.hv3_on)
        self.HV3_on_widg.grid(row=3,column=5)
        self.HV3_off_widg = tk.Button(hvblock,text="HV3 off",command=self.hv3_off)
        self.HV3_off_widg.grid(row=3,column=6)

        w = tk.Label(hvblock,text='HV4 set:').grid(row=4,column=1)
        self.HV4_set_widg = tk.Entry(hvblock,width=6,textvariable=self.var_HV4_set)
        self.HV4_set_widg.bind('<Return>',self.hv4_set)
        self.HV4_set_widg.grid(row=4,column=2)
        w = tk.Label(hvblock,text='actual:').grid(row=4,column=3)
        self.HV4_stat_widg = tk.Entry(hvblock,width=6,textvariable=self.var_HV4_act)
        self.HV4_stat_widg.grid(row=4,column=4)
        self.HV4_on_widg = tk.Button(hvblock,text="HV4 on",command=self.hv4_on)
        self.HV4_on_widg.grid(row=4,column=5)
        self.HV4_off_widg = tk.Button(hvblock,text="HV4 off",command=self.hv4_off)
        self.HV4_off_widg.grid(row=4,column=6)
        
        tblock = tk.Frame(self.frame_widg)
        tblock.grid(row=3,column=1)
        # Detector block
        detblock = tk.LabelFrame(tblock,text="Detector temperature")
        detblock.grid(row=1,column=1)
        w = tk.Label(detblock,text='Set:').grid(row=1,column=1)
        self.detTemp_set_widg = tk.Entry(detblock,width=5,textvariable=self.var_detTemp_set)
        self.detTemp_set_widg.bind('<Return>',self.detTemp_set)
        self.detTemp_set_widg.grid(row=1,column=2)
        w = tk.Label(detblock,text='Actual:').grid(row=1,column=3)
        self.detTemp_stat_widg = tk.Entry(detblock,width=5,textvariable=self.var_detTemp_act)
        self.detTemp_stat_widg.grid(row=1,column=4)
        
        # Temperature block
        tempblock = tk.LabelFrame(tblock,text="Temperatures")
        tempblock.grid(row=1,column=2)
        w = tk.Label(tempblock,text='Base:').grid(row=1,column=1)
        self.baseTemp_stat_widg = tk.Entry(tempblock,width=5,textvariable=self.var_baseTemp_act)
        self.baseTemp_stat_widg.grid(row=1,column=2)
        w = tk.Label(tempblock,text='Amplifier:').grid(row=1,column=3)
        self.ampTemp_stat_widg = tk.Entry(tempblock,width=5,textvariable=self.var_ampTemp_act)
        self.ampTemp_stat_widg.grid(row=1,column=4)
        w = tk.Label(tempblock,text='Power:').grid(row=2,column=1)
        self.powerTemp_stat_widg = tk.Entry(tempblock,width=5,textvariable=self.var_powerTemp_act)
        self.powerTemp_stat_widg.grid(row=2,column=2)
        w = tk.Label(tempblock,text='Communication:').grid(row=2,column=3)
        self.CCTemp_stat_widg = tk.Entry(tempblock,width=5,textvariable=self.var_CCTemp_act)
        self.CCTemp_stat_widg.grid(row=2,column=4)
        
        miscblock = tk.Frame(self.frame_widg)
        miscblock.grid(row=4,column=1)
        w = tk.Label(miscblock,text='Sample rate:').grid(row=1,column=1)
        self.APDCAM_samplerates = [4,2,1,0.5]
        optionList = ('4 MHz', '2 MHz','1 MHz','500 kHz')
        self.APDCAM_samplerate_names = optionList
        self.var_APDCAM_sample.set(optionList[1])
        self.APDCAM_sample_widg = tk.OptionMenu(miscblock,self.var_APDCAM_sample,*optionList)
        self.APDCAM_sample_widg.grid(row=1,column=2)                                    
        self.APDCAM_sample_widg["width"] = 13  
        w = tk.Label(miscblock,text='Ext. clock:').grid(row=1,column=3)
        if (self.GUI_status.config.clockSource == APDCAM_GUI_config_class.CLK_INTERNAL):
            txt = "Not used"
            color = "white"
        else:
            txt = "???"
            color = APDCAM10G_GUI_class.OffColor
        self.APDCAM_extclock_widg = tk.Label(miscblock,text=txt,bg=color,\
                                        width=20)  
        self.APDCAM_extclock_widg.grid(column=4,row=1) 
        
    def set_defaults(self) :
        self.GUI_status.APDCAM_on = False
        self.GUI_status.APDCAM_connected = False
        
    
    def start(self) :
        self.stopThreadSignal = False
        self.updateThread = threading.Thread(target=self.update_APDCAM_widgets)
        self.updateThread.start()
        self.GUI_status.Update_APDCAM = True

    def stop(self) :
        self.APDCAM_off()
        self.stopThreadSignal = True
        #print("Waiting for join...")
        #self.updateThread.join()
        #print("Joined...")
    
    def APDCAM_off(self):
        self.GUI_status.Update_APDCAM = False
        time.sleep(0.5)
        if (self.GUI_status.APDCAM_connected):
            self.GUI_status.APDCAM_reg.close()
        self.GUI_status.APDCAM_connected = False
        self.APDCAM_comm_widg.config(text="Not connected",bg=APDCAM10G_GUI_class.OffColor)
                                         
            
    def APDCAM_on(self,ip=None):
        for i in range(10) :
            if (self.GUI_status.APDCAM_reg == None):
                self.GUI_status.APDCAM_reg = APDCAM10G_regCom()
            self.GUI_status.APDCAM_reg.HV_conversion = [0.12,0.12,0.12,0.12]
            self.APDCAM_comm_widg.config(text="Trying...{:d}".format(i+1),bg=APDCAM10G_GUI_class.TryColor)
            self.APDCAM_comm_widg.update_idletasks()
            print("Connecting...attempt {:d}".format(i+1))
            ret = self.GUI_status.APDCAM_reg.connect()
            print("Connect returned")
            if (ret == ""):
                time.sleep(1) 
                break
            self.GUI_status.APDCAM_reg.close()
            time.sleep(1)  
        if ret != "" :
            self.GUI_status.GUI.add_message(ret)
            self.APDCAM_off()
            return
        self.GUI_status.GUI.add_message("APDCAM connected,")
        self.GUI_status.GUI.add_message(" Firmware: {:s}"\
                                    .format(self.GUI_status.APDCAM_reg.status.firmware.decode('utf-8')))
        
        n = len(self.GUI_status.APDCAM_reg.status.ADC_address) 
        txt = ""
        for i in range(n):
            txt = txt + str(self.GUI_status.APDCAM_reg.status.ADC_address[i])+" "
        self.GUI_status.GUI.add_message(" No of ADCs: {:d}, Addresses: {:s}".format(n,txt))
        self.GUI_status.APDCAM_connected = True
        self.APDCAM_comm_widg.config(text="Connected",bg=APDCAM10G_GUI_class.OnColor)
        err = self.GUI_status.APDCAM_reg.readStatus()
        if (err != "") :
            self.GUI_status.GUI.add_message(err)
            self.APDCAM_off()
            return
        self.GUI_status.APDCAM_status = self.GUI_status.APDCAM_reg.status
        self.var_HV1_set.set("{:5.1f}".format(self.GUI_status.APDCAM_status.HV_set[0]))
        self.var_HV2_set.set("{:5.1f}".format(self.GUI_status.APDCAM_status.HV_set[1]))
        self.var_HV3_set.set("{:5.1f}".format(self.GUI_status.APDCAM_status.HV_set[2]))
        self.var_HV4_set.set("{:5.1f}".format(self.GUI_status.APDCAM_status.HV_set[3]))
        self.var_detTemp_set.set("---")
        self.var_detTemp_set.set("{:5.1f}".format(self.GUI_status.APDCAM_status.ref_temp))
        if (self.GUI_status.config.clockSource == APDCAM_GUI_config_class.CLK_EXTERNAL): 
            err = self.GUI_status.APDCAM_reg.setClock(APDCAM10G_regCom.CLK_EXTERNAL,extmult=4,extdiv=2,autoExternal=True)
        else:
            err = self.GUI_status.APDCAM_reg.setClock(APDCAM10G_regCom.CLK_INTERNAL)
        # This is to correct a problem in the APDTest program, see the comment in APDCAM10G_control.py at the
        # defininiton of the resetStreams() function
        # self.GUI_status.APDCAM_reg.resetStream3()    
        # self.GUI_status.Update_APDCAM = True
        
    def commErrorResponse(self,err):
        if (err != ""):
            self.GUI_status.GUI.add_message(err)
            self.GUI_status.APDCAM_reg.close()
            self.GUI_status.APDCAM_connected = False
            self.APDCAM_comm_widg.config(text="Error",bg=APDCAM10G_GUI_class.OffColor)
        return err
            
            
    def HV_onOff(self,n,on):
        if (self.GUI_status.APDCAM_connected):
            err, d = self.GUI_status.APDCAM_reg.readPDI(self.GUI_status.APDCAM_reg.codes_PC.PC_CARD,\
                                                       self.GUI_status.APDCAM_reg.codes_PC.PC_REG_HVON,\
                                                       1,arrayData=False)
            if (self.commErrorResponse(err) != ""):
                return  
            d = d[0]
            if (on != 0):
               d = d | 2**(n-1)
            else:
               d = d & (2**(n-1) ^ 0xff)
            err = self.GUI_status.APDCAM_reg.writePDI(self.GUI_status.APDCAM_reg.codes_PC.PC_CARD,\
                                                     self.GUI_status.APDCAM_reg.codes_PC.PC_REG_HVON,\
                                                     d,numberOfBytes=1,arrayData=False)
            if (self.commErrorResponse(err) != ""):
               return      
          
    def hv1_on(self):
        self.HV_onOff(1,1)
        
    def hv2_on(self):
        self.HV_onOff(2,1)

    def hv3_on(self):
        self.HV_onOff(3,1)

    def hv4_on(self):
        self.HV_onOff(4,1)
        
    def hv1_off(self):
        self.HV_onOff(1,0) 
        
    def hv2_off(self):
        self.HV_onOff(2,0)
    
    def hv3_off(self):
        self.HV_onOff(3,0)
    
    def hv4_off(self):
        self.HV_onOff(4,0)
        
    def hv_en_ds(self,enable):
        if (self.GUI_status.APDCAM_connected):
            if (enable != 0):
                d = 0xAB
            else:
                d = 0x00
            err = self.GUI_status.APDCAM_reg.writePDI(self.GUI_status.APDCAM_reg.codes_PC.PC_CARD,\
                                                     self.GUI_status.APDCAM_reg.codes_PC.PC_REG_HVENABLE,\
                                                     d,numberOfBytes=1)
            if (self.commErrorResponse(err) != ""):
               return      
                
    def hv_enable(self):
        self.hv_en_ds(1)
    
    def hv_disable(self):
        self.hv_en_ds(0)
        
    def hv1_set(self,event):
        ds = self.var_HV1_set.get()
        self.hv_set(1,ds)
        
    def hv2_set(self,event):
        ds = self.var_HV2_set.get()
        self.hv_set(2,ds)

    def hv3_set(self,event):
        ds = self.var_HV3_set.get()
        self.hv_set(3,ds)

    def hv4_set(self,event):
        ds = self.var_HV4_set.get()
        self.hv_set(4,ds)
    
    def hv_set(self,n,ds):    
        try:
            d = float(ds)
        except ValueError:
            d = 0
        d = int(d/self.GUI_status.APDCAM_reg.HV_conversion[n-1])
#        print("n:"+str(n)+"  d:"+str(d))    

        err = self.GUI_status.APDCAM_reg.writePDI(self.GUI_status.APDCAM_reg.codes_PC.PC_CARD,\
                                                     self.GUI_status.APDCAM_reg.codes_PC.PC_REG_HV1SET+(n-1)*2,\
                                                     d,numberOfBytes=2,arrayData=False)
        if (self.commErrorResponse(err) != ""):
               return  
            
    def detTemp_set(self,x):
        if (self.GUI_status.APDCAM_connected):
            ds = self.var_detTemp_set.get()
            try:
                d = float(ds)
            except ValueError:
                self.GUI_status.GUI.add_message("Invalid detector temperature.")
                return
            if ((d < 15) and (d > 30)) :
                self.GUI_status.GUI.add_message("Detector temperature setting out of range.")
                return
            d = int(d*10)
            err = self.GUI_status.APDCAM_reg.writePDI(self.GUI_status.APDCAM_reg.codes_PC.PC_CARD,\
                                                     self.GUI_status.APDCAM_reg.codes_PC.PC_REG_DETECTOR_TEMP_SET,\
                                                     d,numberOfBytes=2,arrayData=False)
            if (self.commErrorResponse(err) != ""):
               return      
        
    def read_settings(self):
        """ Reads settings from the GUI and Returns an error message and an APDCAM_settings class
        """
        s = APDCAM_settings()
        txt = self.var_APDCAM_sample.get()
        s.samplerate = self.APDCAM_samplerates[self.APDCAM_samplerate_names.index(txt)]
        s.sampleDiv = 20/s.samplerate
        return "",s
        
    def update_APDCAM_widgets(self):
        from time import sleep
        while self.stopThreadSignal == False :
            if (self.GUI_status.Update_APDCAM):
                if (self.GUI_status.APDCAM_connected):
                    self.GUI_status.APDCAM_reg.readStatus()
                    self.GUI_status.APDCAM_status = self.GUI_status.APDCAM_reg.status
                    self.var_HV1_act.set("{:5.1f}".format(self.GUI_status.APDCAM_status.HV_act[0]))
                    self.var_HV2_act.set("{:5.1f}".format(self.GUI_status.APDCAM_status.HV_act[1]))
                    self.var_HV3_act.set("{:5.1f}".format(self.GUI_status.APDCAM_status.HV_act[2]))
                    self.var_HV4_act.set("{:5.1f}".format(self.GUI_status.APDCAM_status.HV_act[3]))
                    if (self.GUI_status.APDCAM_status.temps[APDCAM10G_GUI_class.DETECTOR_TEMP_SENSOR-1] < 100):
                        self.var_detTemp_act.set("{:3.1f}".\
                            format(self.GUI_status.APDCAM_status.temps[APDCAM10G_GUI_class.DETECTOR_TEMP_SENSOR-1]))
                    else:
                        self.var_detTemp_act.set("---") 
                    if (self.GUI_status.APDCAM_status.temps[APDCAM10G_GUI_class.BASE_TEMP_SENSOR-1] < 100):    
                        self.var_baseTemp_act.set("{:3.1f}".\
                            format(self.GUI_status.APDCAM_status.temps[APDCAM10G_GUI_class.BASE_TEMP_SENSOR-1]))
                    else:
                        self.var_baseTemp_act.set("---") 
                    if (self.GUI_status.APDCAM_status.temps[APDCAM10G_GUI_class.AMP_TEMP_SENSOR-1]< 100):
                        self.var_ampTemp_act.set("{:3.1f}".\
                            format(self.GUI_status.APDCAM_status.temps[APDCAM10G_GUI_class.AMP_TEMP_SENSOR-1]))
                    else:
                        self.var_ampTemp_act.set("---") 
                    if (self.GUI_status.APDCAM_status.temps[APDCAM10G_GUI_class.POWER_TEMP_SENSOR-1] < 100):
                        self.var_powerTemp_act.set("{:3.1f}".\
                            format(self.GUI_status.APDCAM_status.temps[APDCAM10G_GUI_class.POWER_TEMP_SENSOR-1]))
                    else:
                        self.var_powerTemp_act.set("---") 
                    self.var_CCTemp_act.set("{:3d}".format(self.GUI_status.APDCAM_status.CCTemp))
                    if (self.GUI_status.config.clockSource == APDCAM_GUI_config_class.CLK_EXTERNAL):
                        if (self.GUI_status.APDCAM_status.extclock_valid) : 
                            clk = self.GUI_status.APDCAM_status.extclock_freq/1000
                            self.APDCAM_extclock_widg.config(text="{:3.2f} MHz".format(clk),\
                                                             bg=APDCAM10G_GUI_class.OnColor)
                        else :
                            self.APDCAM_extclock_widg.config(text="Invalid",bg=APDCAM10G_GUI_class.OffColor)
            time.sleep(0.1)
                    
def gui(show_data_func='show_apdcam'):       
    global root
    root = tk.Tk()
    print("Creating APDCAM-GUI")
    app = APDCAM_GUI_class(master=root,show_data_func=show_data_func)
    app.mainloop()
    
#apdcam10g_control_gui()
