# UC2
<p align="center">
<img src="./IMAGES/UC2_Logo.png" width="200">
</p>

This is the online repository of the Software of the open-source hardware project ''UC2'' [YouSeeToo]. 

[RasPi GUI](./GUI/RASPIapp) | [Hardware Controlling](./HARDWARE_CONTROL/) | [Project Page](https://useetoo.org) | [UC2 CAD Repository](https://github.com/bionanoimaging/UC2-GIT) |[UC2 Paper](https://www.google.com/search?q=comming+soon&oq=comming+soon&aqs=chrome..69i57j0j69i59j0l3.1495j0j4&sourceid=chrome&ie=UTF-8)

Making **open-science** great again! 

## Introduction
For a general introduction on UC2 please check our [CAD-repository](https://github.com/bionanoimaging/UC2-GIT). Our basic belief centers around simple and clean modularity which - combined with creativity and curiosity - can lead to unthought achievements. 



# Getting Started using the Android APP 

We have prepared a very basic control app for **TheBox** to have basic control over the hardware modules. The information can be found [here](./GUI/Android/UC2-TheBox).

<p align="center">
<img src="./GUI/Android/UC2-TheBox/images/Android_GUI.png" width="200" alt="">
</p> 

# Getting Started using the Raspberry Pi GUI

<p align="center">
<img src="./images/UC2_Raspi_Gui_1.png" width="400" alt="">
</p> 


## GUIv1
Our first version for the modular microscope centered around the Raspberry Pi (the hub) controlling [Arduinos](./HARDWARE_CONTROL/ARDUINO/) using I2C-protocol. The Arduinos are then connected to elements (or drivers) like an [8x8 LED-array](./HARDWARE_CONTROL/ARDUINO/ledarr) or [stepper-motors](./HARDWARE_CONTROL/ARDUINO/motors). For image acquisition the [RaspberryPi Camera module v2](https://www.raspberrypi.org/documentation/hardware/camera/) is controlled via picam-package in Python. 

### Setting up Raspberry PI
Due to various design-choices in the beginning we use the [kivy-framework for Python](https://kivy.org/) together with the global installed Python 2.7 in Raspbian. Hence, we prepared a [detailed description (and a script)](./HARDWARE_CONTROL/RASPBERRY_PI) on how to setup your RaspberryPi to work with our framework. </br>
Once the framework is installed, download the [GUI-folder](./GUI/RASPIapp/) into the folder where you want to start it, e.g. "~" (which means your homepath). Then navigate to the GUI folder and run the program via:
```
cd ~/RASPIapp/ 
python main.py
```
Here we assumed, that the micro-controllers controlling e.g. the z-stage or the LED-array have already been setup correctly according to our assembling informations on [CAD-repository](https://github.com/bionanoimaging/UC2-GIT) and connected via I2C. Basic links are given in the next section.

We are in preparation to move the GUI to Python3.6 and virtual environments, so stay tuned! :) 

### Setting up the Micro-Controller
Depending on the micro-controller that will be connected the code that is needed for flashing can be found in different folders.
- Arduino -> [8x8 LED-Array (e.g.: ?)](./HARDWARE_CONTROL/ARDUINO/ledarr)
- Arduino -> [Stepper-Motors (x,y,z; e.g.: ?)](./HARDWARE_CONTROL/ARDUINO/ledarr)
- Arduino -> [General Minimals](./HARDWARE_CONTROL/ARDUINO/minimals)

Further, we rely on some extra Arduino-libraries that can be found in the [libraries folder](./HARDWARE_CONTROL/ARDUINO/libraries).

## Structure of Repository
	
	* GUI
		* RASPIapp (GUI to control e.g. the Incubator Microscope) 
		* Android APP
	* HARDWARE_CONTROL
		* ARDUINO
		* ESP32
		* RASPBERRY_PI
	* WORKSHOPS
		* 01_INLINE_HOLOGRAMM
		* 02_LIGHTSHEET
	* SCRIPTS
		

## Get Involved!
This project is open so that anyone can get involved. Ways you can contribute include (see also: https://github.com/rwb27/openflexure_microscope):

* Get involved in discussions in the ISSUE-section
* Raise an issue if you spot something that's wrong, or something that could be improved. This includes the instructions/documentation.
* We support you with the basic CAD Design files, so that you can develop specific hardware-function which can fit in our cubes (Autocad Inventor files are not accessible though) 
* Suggest better text or images for the instructions.
* Improve the design of parts - even if you don't use OpenSCAD, STL files or descriptions of changes are helpful.
* Fork it, and make pull requests - again, documentation improvements are every bit as useful as revised OpenSCAD files.
* Things in need of attention are currently described in issues so have a look there if you'd like to work on something but aren't sure what.

## Credits
R. Heintzmann, X. Uwurukundo, H. Wang, B. Marsikova, B. Diederich, Lichtwerkstatt, IPHT Jena