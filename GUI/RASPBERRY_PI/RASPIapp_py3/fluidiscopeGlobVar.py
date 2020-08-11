# here the global variables are defined
import socket
import datetime
import unipath as uni
import os

global VERSION
global EVENT
global APP

global my_dev_flag
global started_first_exp
global is_use_picamera
global is_use_vimba
global vimba_preview
global vimba_is_record_preview

global config
global camera
global motors
global ledarr
global fluo
global mqttclient

global code_path
global project_path
global config_path
global data_path
global expt_path
global save_path
global copy_path
global expt_num
global today
global i2c
global active_imaging_method 
#global setup_number

# datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") -> important for saving the expimernts
today = datetime.datetime.now().strftime("%Y%m%d")
if os.name == 'nt':
    my_dev_flag = True
else:
    my_dev_flag = False
started_first_exp = False
is_use_picamera = False
is_use_vimba = True

i2c = True
#setup_number = "004"
VERSION = '0.4'
config = []
EVENT = {}
APP = []
motors = []
ledarr = []
fluo = []

active_imaging_method = 'FULL' # For vimba intensity weighting