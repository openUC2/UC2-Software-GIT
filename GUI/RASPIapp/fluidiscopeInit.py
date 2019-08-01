import os
import platform
import datetime
import time
import serial
import socket

from kivy.config import Config
import fluidiscopeGlobVar as fg
import fluidiscopeIO
import unipath as uni

if not fg.my_dev_flag:
    import picamera
    from I2CBus import I2CBus
    from I2CDevice import I2CDevice


# Initialization routine of Fluidiscope


def arduino_init():
    arch = os.uname()[4]
    if "arm" in arch:
        fg.camera = picamera.PiCamera()
        print("cam is online")
        # address = I2CBus.scanBus()
        fg.ledarr = I2CDevice(0x07) #normally 0x07 -> changed for fluo system 10.07.2019
        fg.motors = I2CDevice(0x08) #normally 0x08 -> changed for fluo system 10.07.2019
        time.sleep(1.0) #because accessing same device
        fg.fluo = I2CDevice(0x08)   #sits on the same
        #TODO: WHAT THE HACK?!
        #fg.ledarr.announce()
        #fg.motors.announce()
        #fluidiscopeIO.send(fg.ledarr, "CLEAR")



def GUI_define_sizes():
    Config.set('graphics', 'width', '800')
    Config.set('graphics', 'height', '480')
    Config.set('graphics', 'borderless', 'True')
    Config.write()


def load_config():
    test_text = ""
    fg.code_path = uni.Path.cwd()
    fg.project_path = fg.code_path.parent
    fg.data_path = uni.Path(fg.code_path, "data")
    fg.save_path = uni.Path(fg.data_path, str(fg.today))
    fg.config_path = uni.Path(fg.code_path, "config")
    fg.config_file = uni.Path(fg.config_path, "main_config.yaml")
    fg.config = fluidiscopeIO.load_config(fg.config_file)
    fg.autofocus_path = uni.Path(fg.code_path, "autofocus")
    fg.copy_path = ""

    if not fg.config:
        fluidiscopeIO.restore_config()
        test_text = "from backup "
        fg.config = fluidiscopeIO.load_config(fg.config_file)
    print("Configuration file {0}loaded".format(test_text))