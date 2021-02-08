import kivy
kivy.require('1.0.6') # replace with your current kivy version !

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle


# Quick hack to switch to USB
from SerialDevice import SerialDevice
import time
import serial

is_serial = True
serialadress = '/dev/ttyUSB0'
serialdevice = None

global lensX1
lensX1 = 0 
global lensZ1 
lensZ1 = 0


# Very hacky to have always the same Serial device..
try:
	serialdevice = serial.Serial(serialadress, 115200, timeout=.1)
	time.sleep(2)
except:
	serialdevice = 1


try:
    esp_lens = SerialDevice(serialdevice)  # normally 0x07
except Exception as e:
    print(e)
    esp_lens = False
    logger.debug("esp_lens is not connected!")

'''
for iz in range(zstart,zend,zstep):
    fluo.send("LENS1Z", int(iz))
    time.sleep(0.1)
    for ix in range(xstart,xend,xstep):
        fluo.send("LENS1X", int(ix))
        time.sleep(0.1)
'''

# This callback will be bound to the LED toggle and Beep button:
def press_callback(obj):
	global lensX1
	global lensZ1

	print("Button pressed,", obj.text)
	if obj.text == 'LensZ-':
		lensZ1-=1
		esp_lens.send("LENS1Z", int(lensZ1))
	if obj.text == 'LensZ+':
		lensZ1+=1
		esp_lens.send("LENS1Z", int(lensZ1))
		
# This is called when the slider is updated:
def update_lensX1(obj, value):
	global lensX1
	try:
		esp_lens.send("LENS1X", int(obj.value))
	except:
		print("Updating lensX1 to:" + str(obj.value))
	lensX1 = obj.value

def update_lensZ1(obj, value):
	global lensZ1
	try:
		esp_lens.send("lensZ1", int(obj.value))
	except:
		print("Updating lensZ1 to:" + str(obj.value))
	lensZ1 = obj.value


class MyApp(App):

	def build(self):
		# Set up the layout:
		layout = GridLayout(cols=3, rows=3, spacing=30, padding=30, row_default_height=150)


		# Create the rest of the UI objects (and bind them to callbacks, if necessary):		
		lensX1Slider = Slider(orientation='horizontal', min=0, max=2**16, value=lensX1)
		lensX1Slider.bind(on_touch_down=update_lensX1, on_touch_move=update_lensX1)
			
		lensZ1Slider = Slider(orientation='horizontal', min=0, max=2**16, value=lensZ1)
		lensZ1Slider.bind(on_touch_down=update_lensZ1, on_touch_move=update_lensZ1)
		
		lensZ1ButtonMinus = Button(text="LensZ-")
		lensZ1ButtonMinus.bind(on_press=press_callback)
		lensZ1ButtonPlus = Button(text="LensZ+")
		lensZ1ButtonPlus.bind(on_press=press_callback)


		# Add the UI elements to the layout:
		layout.add_widget(lensZ1ButtonMinus)
		layout.add_widget(lensX1Slider)
		layout.add_widget(lensZ1ButtonPlus)

		layout.add_widget(Button(text='-', size_hint_x=None, width=100))
		layout.add_widget(lensZ1Slider)
		layout.add_widget(Button(text='-', size_hint_x=None, width=100))

		#layout.add_widget(lensX1Slider)

		return layout

if __name__ == '__main__':
	MyApp().run()