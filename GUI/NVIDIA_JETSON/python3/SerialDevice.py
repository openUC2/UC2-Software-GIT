import os
import sys
import time
import errno
import fluidiscopeGlobVar as fg
import logging
import serial 

logger = logging.getLogger('UC2_SerialDevice')


class SerialDevice(object):
    max_msg_len = 32
    delim_strt = "*"
    delim_stop = "#"
    delim_cmds = ";"
    delim_inst = "+"

    com_cmds = {"STATUS": "STATUS", "LOGOFF": "LOGOFF", "NAME": "NAME"}

    def __init__(self, serialdevice):
        
        self.name = "unknown"
        self.outBuffer = ""
        self.myserialdevice = serialdevice


    def isEmpty(self, byte_list):
        if (byte_list):
            cutoff = len(self.delim_strt) + len(self.delim_stop)
            byte_list = byte_list[cutoff:]
            return (byte_list.count(255) == len(byte_list))
        return False

    def requestEvent(self):
        try:
            print("Nothing happens here..")
            #byte_msg = I2CBus.defaultBus.read_i2c_block_data(
            #    self.address, 0, SerialDevice.max_msg_len)
        except Exception as e:
            print("Unknown error {0} occured on request on address {1}".format(
                e, hex(self.address)))
            return

        if self.isEmpty(byte_msg):
            print("Device on address {0} is not responding. (message is empty).".format(
                hex(self.address)))
        else:
            try:
                str_msg = [chr(x) for x in byte_msg]
                strt = min(i for i, c in enumerate(
                    str_msg) if c == self.delim_strt)
                stop = max(i for i, c in enumerate(
                    str_msg) if c == self.delim_stop)
                str_msg = str_msg[strt + 1:stop]
                str_msg = "".join(str_msg)
            except Exception as e:
                print(
                    "Unknown error {0} occured on decoding of received response on address {1}. Is start or stop signal missing?".format(
                        e, hex(self.address)))
                return
            return str_msg
        return

    def sendEvent(self, value):
        try:
            self.outBuffer = self.delim_strt + str(value) + self.delim_stop
            print("Printing Buffe:"+self.outBuffer)
            self.outBuffer = [ord(x) for x in self.outBuffer]
            self.myserialdevice.write(self.outBuffer)
            self.outBuffer = ""
        except Exception as e:
            print("Unknown error {0} occured on send to address {1}".format(
                e, hex(self.address)))
        return

    def extractCommand(self, args):
        cmd = ""
        delim = SerialDevice.delim_inst
        for i, arg in enumerate(args):
            if type(arg) == list:
                sep = [str(x) for x in arg]
                cmd += delim.join(sep)
            else:
                cmd += str(arg)
            cmd += delim

        return cmd[:-1]

    def send(self, *args):
        cmd = self.extractCommand(args)
        try:
            print("Sending:   {0}".format(cmd))
            logger.info("Sending:   {0}".format(cmd))
            self.sendEvent(cmd)
        except:
            print(
                "Debugging mode. Generated Command=[{}] has not been sent.".format(cmd))


    def request(self):
        ans = self.requestEvent()
        if ans and (ans != "BUSY"):
            print("Receiving: {0}".format(ans))
            return ans

    def sendCommand(self, *args):
        self.send(*args)
        time.sleep(0.0025)
        return self.request()
