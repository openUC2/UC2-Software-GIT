import os
import sys
import time
import errno
import fluidiscopeGlobVar as fg
import paho.mqtt.client as mqtt


class MQTTDevice(object):
    '''
    Class that communicates with MQTT devices while mimicing the calling syntax from I2CDevice
    '''
    # delimiters
    # delim_strt = "*"
    # delim_stop = "#"
    delim_cmds = ";"
    delim_inst = "+"
    # common commands
    com_cmds = {"STATUS": "STATUS", "LOGOFF": "LOGOFF", "NAME": "NAME"}
    # MQTT-data
    topic_send = "RECM"  # topic for commands received by device
    topic_status = "STAT"
    topic_announce = "ANNO"

    def __init__(self, setup, device):
        self.setup = setup
        self.device = device
        self.topic_base = "/" + self.setup + "/" + self.device + "/"
        self.mqtt_subscribe()

    def mqtt_subscribe(self, *args):
        fg.mqttclient.subscribe(self.topic_base + self.topic_announce)
        fg.mqttclient.subscribe(self.topic_base + self.topic_status)

    def send(self, *args):
        self.payload = self.extractCommand(args)
        # if fg.my_dev_flag:
        #    print(
        #        "Debugging mode. Generated Command=[{}] has not been sent.".format(cmd))
        # else:
        # print("MQTTclient: Topic={0}, Payload=".format(cmd))
        fg.mqttclient.publish(self.topic_base + self.topic_send, self.payload)

    def extractCommand(self, args):
        cmd = ""
        delim = MQTTDevice.delim_inst  # so that it is not different per instances
        print("MQTTclient_extractCommand -> starting for: ")
        print(args)
        for i, arg in enumerate(args):
            if type(arg) == list:
                sep = [str(x) for x in arg]
                # if i == 0:
                #    self.topic = self.topic_base + sep[0]
                #    sep = sep[1:]
                cmd += delim.join(sep)
            else:
                # if i == 0:
                #    sep = arg.split(MQTTDevice.delim_inst)
                #    self.topic = self.topic_base + sep[0]
                #    arg = delim.join(sep[1:])
                #    arg += delim if not (arg == "") else ""
                cmd += str(arg)
           # if i > 0:
            cmd += delim
            print("MQTTDevice_extractCommand -> i={}: topic_spec={}, cmd={}.".format(i,
                                                                                     self.topic_base, cmd[:-1]))  # verbose output -> maybe rather put into logfile?
        return cmd[:-1]

    # def request(self):
    #    ans = self.requestEvent()
    #    if ans and (ans != "BUSY"):
    #        print("Receiving: {0}".format(ans))
    #        return ans

    # def sendCommand(self, *args):
    #    self.send(*args)
    #    time.sleep(0.0025)
    #    return self.request()
