import time
import paho.mqtt.client as mqtt
from picamera import PiCamera
import sys
import os
# ----------------------------------------------------------------------------
# predefine some variables
topic_preview = "/setup1/cam1/preview"
topic_takeimage = "/setup1/cam1/takeimage"
topic_takeimageseries = "/setup1/cam1/takeimageseries"
topic_takevideo = "/setup1/cam1/takevideo"

#PiCamera.active = False # class is set to read only
camera = PiCamera()
dic_param = {
    'camParam': {'resolution': [1024,768], 'active': False, 'image_format': 'jpg','vid_active': False, 'vid_format':'h264'},
    'fileParam': {'dataPath':"./data/",'dataPathChk':False}}
# ----------------------------------------------------------------------------
# predefine some functions
def on_connect(client,userdata,flags,rc):
    if rc==0: # connection established
        client.connected_flag=True
        print("Connected with result code = {0}".format(rc))
    else: 
        print("Connection error")
        client.bad_connection_flag=True

def on_message(client,userdata,message):
    #print("on message")
    #a = time.time()
    #print("Time on receive={0}".format(a))
    if message =="off" :
        client.turnoff_flag=True
    print("Received={0}\nTopic={1}\nQOS={2}\nRetain Flag={3}".format(message.payload.decode("utf-8"),message.topic,message.qos,message.retain))
    # enable or disable preview
    if message.topic == topic_preview: 
        camera_setParam('preview')
        if(dic_param['camParam']['active']):
            camera.stop_preview()
            dic_param['camParam']['active'] = False
        else:
            camera.start_preview()
            dic_param['camParam']['active'] = True
    # take image
    elif message.topic == topic_takeimage: 
        camera_setParam('take_image')
        im_name = get_filename() + "image." + dic_param['camParam']['image_format'] #change format here
        print("Image-Path={}".format(im_name))
        camera.capture(im_name)
    # take e.g. Light-sheet series (moving the motor in-between)
    elif message.topic == topic_takeimageseries:
        # here comes the lightsheet-series -> integration with ESP32 mqtt-commands
        pass
    # take e.g. Light-sheet series (record a video)
    elif message.topic == topic_takevideo:
        camera_setParam('take_video')
        vid_name = get_filename() + "video." + dic_param['camParam']['vid_format']      
        print("Video-Path={}".format(vid_name))
        if(dic_param['camParam']['vid_active']):
            camera.stop_recording()
            dic_param['camParam']['vid_active'] = False
        else:
            camera.start_recording(vid_name)
            dic_param['camParam']['vid_active'] = True
        sys.stdout.flush()
    else:
        print("Topic unknown")

def on_disconnect(client,userdata,rc):
    #logging.info("disconnecting reason: {0}".format)
    print("disconnecting reason: {0}".format)
    client.connected_flag = False
    client.disconnect_flag= True

def camera_setParam(myswitch):
    if(myswitch == "preview"): # only preview on raspberry
        pass
    else: # take image 
        pass

def get_filename():
    file_path = dic_param['fileParam']['dataPath']
    if not dic_param['fileParam']['dataPathChk']:
        chk_dir(file_path)
        dic_param['fileParam']['dataPathChk'] =True
    return file_path + time.strftime("%Y%m%d_%H%M%S", time.localtime()) + '--'

def chk_dir(data_path):
    try:
        if not os.path.exists(data_path):
            os.makedirs(data_path)
            print('Folder: {0} created successfully'.format(data_path))
    finally:
        print('Folder check done!')
# ----------------------------------------------------------------------------
# Config Camera
#camera_setParam()
# ----------------------------------------------------------------------------
# MQTT-class -> add  general definitions and variables (=DEFAULTS)
mqtt.Client.connected_flag=False    #create flag in class
mqtt.Client.bad_connection_flag=False #new flag
mqtt.Client.disconnect_flag=False
mqtt.Client.turnoff_flag=False
# define broker
broker="192.168.50.1"
client1_name="raspi1"
client1_pass="1ipsar"
client1 = mqtt.Client("Raspi1") # creates a new client
client1.username_pw_set(client1_name,client1_pass)
# attach functions to client
client1.on_connect = on_connect
client1.on_message = on_message
client1.on_disconnect = on_disconnect
# start loop to process received messages
client1.loop_start()
# connect
try:
    print("connecting to broker ",broker)
    client1.connect(broker,port=1883,keepalive=60)
    while not client1.connected_flag and not client1.bad_connection_flag:
        print("Waiting for established connection.")
        time.sleep(1)
    if client1.bad_connection_flag:
        client1.loop_stop()
        sys.exit()
    else:
        # subscribe to topics
        print("subscribing to {}, {}, {}".format(topic_takeimage,topic_preview,topic_takevideo))
        client1.subscribe([(topic_takeimage,0),(topic_preview,0),(topic_takevideo,0)])
        #time.sleep(2) # let device settle a bit
        # publish to test-topic
        #test_payload = "-20"
        #print("published={0} to {1}".format(test_payload,test_topic))
        #a = time.time()
        #print("Time before publish={0}".format(a))
        #client1.publish(test_topic,test_payload) #publish
        #a = time.time()
        #print("Time after publish={0}".format(a))
        #time.sleep(4)
        a = time.time()
        period = 10
        while not client1.turnoff_flag: #long loop
            time.sleep(0.02) #update only every 20ms
            if (time.time()-a > 10):
                print("I am alive.")
                a = time.time()
        
except Exception as err: # e.g. arises when port errors exist etc
    print("Connection failed")
    print(err)

# disconnect and stop loop
if client1.turnoff_flag:
    client1.disconnect()
    client1.loop_stop()
