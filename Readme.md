# UC2
<p align="center">
<img src="./IMAGES/UC2_Logo.png" width="200">
</p>

This is the online repository of the Software of the open-source hardware project ''UC2'' [YouSeeToo]. 

[RasPi GUI](./GUI/RASPBERRY_PI/README.md) | [Hardware Controlling](./HARDWARE_CONTROL/) | [Project Page](https://useetoo.org) | [UC2 CAD Repository](https://github.com/bionanoimaging/UC2-GIT) |[UC2 Paper](https://www.biorxiv.org/content/10.1101/2020.03.02.973073v1)

Making **open-science** great again! 

## Introduction
For a general introduction on UC2 please check our [CAD-repository](https://github.com/bionanoimaging/UC2-GIT). Our basic belief centers around simple and clean modularity which - combined with creativity and curiosity - can lead to unthought achievements. 


# Getting Started
Like with our toolbox we tried to keep our interfaces modular as well. Hence, hardware (like Motors, LED, ...) can be adressed using 
*   Arduino (and alike) via I2C (Hardwired)
*   ESP32 (and alike) via MQTT (WiFI)

and could even be a mixture of both.Further, to control this components we provide two different graphical user interfaces (GUI):
*   Raspberry Pi (RasPi) 
*   Android App 

All useful links will be provided after the general shape of the repository is shortly displayed.

## Structure of Repository
	
	* 	coming
		*	soon


# Getting Started using the Raspberry Pi GUI

<p align="center">
<img src="./images/UC2_Raspi_Gui_1.png" width="400" alt="">
</p> 

Find a detailed description [here](./GUI/RASPBERRY_PI)


# Getting Started using the Android APP 

We have prepared a very basic control app for **TheBox** to have basic control over the hardware modules. The information can be found [here](./GUI/Android/UC2-TheBox).

<p align="center">
<img src="./GUI/Android/UC2-TheBox/images/Android_GUI.png" width="200" alt="">
</p> 		

# Setting up the Micro-Controller
Depending on the micro-controller that will be connected the code that is needed for flashing can be found in different folders.
* [The ESP32 + MQTT PATH](./HARDWARE_CONTROL/ESP32/README.md)
* [The ARDUINO + I2C PATH](./HARDWARE_CONTROL/ARDUINO/README.md)


# Get Involved!
Our software-oriented UC2-SOFTWARE-GIT provides you with all the different programs that you need to automate your blocks. Run our GUI on RasPi or Android-Phone and setup your Arduino or ESP32. We want to generalize our Software to even integrate more with community standards and have an overall compatibility with different Operating Systems. 

Get **INVOLVED** by help us to:
*   switch to a new browser-based GUI
*   improve our MQTT based connection routines and trying to improve the necessary hardware-flashes
*   add totally unknown functions
*   make our Software as modular as possible

## Credits
R. Heintzmann, X. Uwurukundo, H. Wang, N. Schramma, E. Bingoel, B. Marsikova, B. Diederich, Lichtwerkstatt, IPHT Jena
