# based on: ------------------------------------------------------------------
# - http://www.steves-internet-guide.com/into-mqtt-python-client/
# - http://www.steves-internet-guide.com/client-connections-python-mqtt/
# - http://www.steves-internet-guide.com/python-mqtt-publish-subscribe/
# - http://www.steves-internet-guide.com/simple-python-mqtt-topic-logger/
# ----------------------------------------------------------------------------
import time
import paho.mqtt.client as mqtt
import sys
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
    a = time.time()
    print("Time on receive={0}".format(a))
    if message =="off" :
        client.turnoff_flag=True
    print("Received={0}\nTopic={1}\nQOS={2}\nRetain Flag={3}".format(message.payload.decode("utf-8"),message.topic,message.qos,message.retain))

def on_disconnect(client,userdata,rc):
    #logging.info("disconnecting reason: {0}".format)
    print("disconnecting reason: {0}".format)
    client.connected_flag = False
    client.disconnect_flag= True
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
        # subscribe to test-topic
        test_topic = "setup1/motor/move"
        print("subscribing to {0}".format(test_topic))
        client1.subscribe(test_topic)
        #time.sleep(2) # let device settle a bit
        # publish to test-topic
        test_payload = "-20"
        print("published={0} to {1}".format(test_payload,test_topic))
        a = time.time()
        print("Time before publish={0}".format(a))
        client1.publish(test_topic,test_payload) #publish
        a = time.time()
        print("Time after publish={0}".format(a))
        time.sleep(4)
        
except Exception as err: # e.g. arises when port errors exist etc
    print("Connection failed")
    print(err)

# disconnect and stop loop
if client1.turnoff_flag:
    client1.disconnect()
    client1.loop_stop()
