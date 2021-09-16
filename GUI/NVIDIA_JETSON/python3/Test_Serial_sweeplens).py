# Quick hack to switch to USB
from SerialDevice import SerialDevice
import time
import serial

is_serial = True
serialadress = '/dev/ttyUSB0'
serialdevice = None

zstart=100
zend=120
zstep=1

xstart=500
xend=2500
xstep=50
# Very hacky to have always the same Serial device..
serialdevice = serial.Serial(serialadress, 115200, timeout=.1)

time.sleep(2)

try:
    ledarr = SerialDevice(serialdevice)  # normally 0x07
except Exception as e:
    print(e)
    ledarr = False
    logger.debug("LEDARray is not connected!")

# connect to Motors        
try:
    motors = SerialDevice(serialdevice)  # normally 0x08
except:
    motors = False
    logger.debug("Motors are not connected!")
    
# connect to Fluo
try:
    fluo = SerialDevice(serialdevice)
except:
    fluo = False
    logger.debug("Fluo module isnot connected!")
    


while(True):
    fluo.send("LENS1Z", int(zstart))
    time.sleep(0.1)
    for ix in range(xstart,xend,xstep):
        fluo.send("LENS1X", int(ix))
        time.sleep(0.1)
 
    for ix in range(xstart,xend,xstep):
        fluo.send("LENS1X", int(xend-ix+xstart))
        time.sleep(0.1)
