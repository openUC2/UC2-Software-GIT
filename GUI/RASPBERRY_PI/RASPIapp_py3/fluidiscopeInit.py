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

if fg.i2c:
    from I2CDevice import I2CDevice
    from I2CBus import I2CBus
else:
    from MQTTDevice import MQTTDevice
    import paho.mqtt.client as mqtt

if not fg.my_dev_flag:
    import picamera


# Initialization routine of Fluidiscope


def arduino_init():
    # address = I2CBus.scanBus()
    fg.ledarr = I2CDevice(0x07)  # normally 0x07
    fg.motors = I2CDevice(0x08)  # normally 0x08
    # time.sleep(1.0) #because accessing same device
    # sits on the same Arduino as motors for now
    fg.fluo = I2CDevice(0x08)
    # fg.ledarr.announce()
    # fg.motors.announce()
    #fluidiscopeIO.send(fg.ledarr, "CLEAR")

# MQTT Functions ------------------------------------------------------------------------------


def mqtt_init():
    # connect to server
    import random
    setup_name = "S" + fg.setup_number
    device_ID = "RASPI_" + str(random.randint(0, 100000))
    device_MQTT_name = "RAS01"
    mqtt_connect_to_server(broker="0.0.0.0", mqttclient_name="raspi1",
                           mqttclient_pass="1ipsar", mqttclient_ID=device_ID, port=1883, keepalive=60)
    # register Raspberry
    fg.raspi = MQTTDevice(setup_name, device_MQTT_name)
    # instanciate devices
    fg.ledarr = MQTTDevice(setup_name,  "LAR01")
    fg.motors = [MQTTDevice(setup_name, "MOT02"), MQTTDevice(
        setup_name, "MOT02"), MQTTDevice(setup_name, "MOT01")]
    fg.fluo = MQTTDevice(setup_name, "MOT01")


def mqtt_connect_to_server(broker, mqttclient_name, mqttclient_pass, mqttclient_ID, port=1883, keepalive=60):
    mqtt.Client.connected_flag = False  # create flag in class
    mqtt.Client.bad_connection_flag = False  # new flag
    mqtt.Client.disconnect_flag = False
    mqtt.Client.turnoff_flag = False
    # define broker
    fg.mqttclient = mqtt.Client(mqttclient_ID)  # creates a new client
    fg.mqttclient.username_pw_set(mqttclient_name, mqttclient_pass)
    # attach functions to client
    fg.mqttclient.on_connect = on_connect
    fg.mqttclient.on_message = on_message
    fg.mqttclient.on_disconnect = on_disconnect
    # start loop to process received messages
    fg.mqttclient.loop_start()
    try:
        print("MQTTClient: connecting to broker ", broker)
        fg.mqttclient.connect(broker, port, keepalive)
        while not fg.mqttclient.connected_flag and not fg.mqttclient.bad_connection_flag:
            print("MQTTClient: Waiting for established connection.")
            time.sleep(1)
        if fg.mqttclient.bad_connection_flag:
            fg.mqttclient.loop_stop()
            print("MQTTClient: had bad-connection. Not trying to connect any further.")
    except Exception as err:  # e.g. arises when port errors exist etc
        print("MQTTClient: Connection failed")
        print(err)

    # TODO: spawn Thread that checks for connection status
    # add:
    # if client1.turnoff_flag:
    #    client1.disconnect()
    #    client1.loop_stop()


def on_connect(client, userdata, flags, rc):
    if rc == 0:  # connection established
        client.connected_flag = True
        print("Connected with result code = {0}".format(rc))
    else:
        print("Connection error")
        client.bad_connection_flag = True


def on_message(client, userdata, message):
    #print("on message")
    a = time.time()
    print("Time on receive={0}".format(a))
    if message == "off":
        client.turnoff_flag = True
    print("Received={0}\nTopic={1}\nQOS={2}\nRetain Flag={3}".format(
        message.payload.decode("utf-8"), message.topic, message.qos, message.retain))


def on_disconnect(client, userdata, rc):
    #logging.info("disconnecting reason: {0}".format)
    print("disconnecting reason: {0}".format)
    client.connected_flag = False
    client.disconnect_flag = True
# MQTT Functions end ---------------------------------------------------------------------------------


def camera_init():
    try:
        arch = os.uname()[4]
    except:
        arch = os.name
    if "arm" in arch:
        fg.camera = picamera.PiCamera()
        print("cam is online")


def controller_init():
    if fg.i2c:
        arduino_init()
    else:  # case of e.g. ESP32
        mqtt_init()
    camera_init()


def GUI_define_sizes():
    Config.set('graphics', 'width', '800')
    Config.set('graphics', 'height', '480')
    Config.set('graphics', 'borderless', 'True')
    Config.write()
    pass


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

    # add further security changes
    # should always be empty if no imaging technique is chosen
    fg.config['experiment']['active_methods'] = []
