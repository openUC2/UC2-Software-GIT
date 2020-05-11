<p align="left">
<img src="./IMAGES/UC2_logo_text.png" width="400">
</p>

# **UC2 - Open and Modular Optical Toolbox**

---
[<img src="./IMAGES/UC2_Logo.png" height=40>](https://www.useetoo.org) [<img src="./IMAGES/icon_git.png" width=40>](https://github.com/bionanoimaging/UC2-GIT) [<img src="./IMAGES/icon_UC2Software.png" height=40>](https://github.com/bionanoimaging/UC2-Software-GIT) [<img src="./IMAGES/icon_tw.png" width=40>](https://twitter.com/openuc2)  [<img src="./IMAGES/icon_yt.png" width=40>](https://www.youtube.com/channel/UCcHFzXTdC1Ro0OMnHS_54UA) [![Open Source Love](https://badges.frapsoft.com/os/v3/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/)

---

This is the online repository of the Software of the open-source hardware project ''UC2'' [YouSeeToo].

[RasPi GUI](./GUI/RASPBERRY_PI/README.md) | [Hardware Controlling](./HARDWARE_CONTROL/) | [UC2 Paper](https://www.biorxiv.org/content/10.1101/2020.03.02.973073v1)

---

## Making **open-science** great again!
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
<img src="./IMAGES/UC2_Raspi_Gui_1.png" width="400" alt="">
</p>

Find a detailed description [here](./GUI/RASPBERRY_PI/README.md)


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
This project is open so that anyone can get involved. You don't even have to learn CAD designing or programming. Find ways you can contribute in  [CONTRIBUTING](https://github.com/bionanoimaging/UC2-GIT/blob/master/CONTRIBUTING.md)

Our software-oriented UC2-SOFTWARE-GIT provides you with all the different programs that you need to automate your blocks. Run our GUI on RasPi or Android-Phone and setup your Arduino or ESP32. We want to generalize our Software to even integrate more with community standards and have an overall compatibility with different Operating Systems.

Get **INVOLVED** by help us to:
*   switch to a new browser-based GUI
*   improve our MQTT based connection routines and trying to improve the necessary hardware-flashes
*   add totally unknown functions
*   make our Software as modular as possible

## Credits
R. Heintzmann, X. Uwurukundo, H. Wang, N. Schramma, E. Bingoel, B. Marsikova, B. Diederich, Lichtwerkstatt, IPHT Jena
