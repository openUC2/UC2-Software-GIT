<p align="left">
<img src="./IMAGES/UC2_logo_text.png" width="400">
</p>

# **UC2 - Open and Modular Optical Toolbox**

---
[<img src="./IMAGES/sitemap.png" height=50 align="right">](./SITEMAP.md)

[<img src="./IMAGES/UC2_Logo.png" height=40>](https://www.useetoo.org) [<img src="./IMAGES/icon_git.png" width=40>](https://github.com/bionanoimaging/UC2-GIT) [<img src="./IMAGES/icon_UC2Software.png" height=40>](https://github.com/bionanoimaging/UC2-Software-GIT) [<img src="./IMAGES/icon_tw.png" width=40>](https://twitter.com/openuc2)  [<img src="./IMAGES/icon_yt.png" width=40>](https://www.youtube.com/channel/UCcHFzXTdC1Ro0OMnHS_54UA) [![Open Source Love](https://badges.frapsoft.com/os/v3/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/)

Cite this repository: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4041343.svg)](https://doi.org/10.5281/zenodo.4041343)

---

This is the online repository of the Software of the open-source hardware project ''UC2'' (You.See.Too.). For a general introduction on UC2 please check our [main repository](https://github.com/bionanoimaging/UC2-GIT).

## Click here if you're looking for
[RasPi GUI](./GUI/RASPBERRY_PI) | [Android App](./GUI/Android/UC2-TheBox)  | [Hardware Controlling](./HARDWARE_CONTROL)| [Something else](./SITEMAP.md)
:------:|:------:|:------:|:------:
[<img src="./IMAGES/UC2_Raspi_Gui_1.jpg" height="150" hspace="20">](./GUI/RASPBERRY_PI)|[<img src="./GUI/Android/UC2-TheBox/images/Android_GUI.png" height="150">](./GUI/Android/UC2-TheBox)|[<img src="./IMAGES/HW_Controll.png" height="150">](./HARDWARE_CONTROL)|[<img src="./IMAGES/sitemap.png" width="150">](./SITEMAP.md)


## [Get Involved! Contribute to the project!](CONTRIBUTING.md)

## ... or keep on reading to get started!


---

## Making **open-science** great again!
For a general introduction on UC2 please check our [main repository](https://github.com/bionanoimaging/UC2-GIT). Our basic belief centers around simple and clean modularity which - combined with creativity and curiosity - can lead to unbelievable achievements. Read more in the UC2 paper: [A versatile and customizable low-cost 3D-printed open standard for microscopic imaging](https://www.nature.com/articles/s41467-020-19447-9) [![DOI:10.1038/s41467-020-19447-9](http://img.shields.io/badge/DOI-10.1038/s41467_020_19447_9-000000.svg)](https://doi.org/10.1038/s41467-020-19447-9).

# Getting Started
Like with our toolbox we tried to keep our interfaces modular as well. Therefore, hardware (like Motors, LED, ...) can be adressed using
*   Arduino (and alike) via I2C (Hardwired)
*   ESP32 (and alike) via MQTT (WiFI)

and could even be a mixture of both.Further, to control this components we provide two different graphical user interfaces (GUI):
*   Raspberry Pi (RasPi)
*   Android App

All useful links will be provided after the general shape of the repository is shortly displayed.

# Getting Started using the Raspberry Pi GUI

<p align="center">
<img src="./IMAGES/UC2_Raspi_Gui_1.jpg" width="400" alt="">
</p>

Find a detailed description [here](./GUI/RASPBERRY_PI)

# Getting Started using the Android APP

We have prepared a very basic control app for **TheBox** to have basic control over the hardware modules. The information can be found [here](./GUI/Android/UC2-TheBox).

<p align="center">
<img src="./GUI/Android/UC2-TheBox/images/Android_GUI.png" width="200" alt="">
</p> 		

# Setting up the Micro-Controller
Depending on the micro-controller that will be connected the code that is needed for flashing can be found in different folders.
* [The ESP32 + MQTT PATH](./HARDWARE_CONTROL/ESP32)
* [The ARDUINO + I2C PATH](./HARDWARE_CONTROL/ARDUINO)

### Complete overview of setups, modules, parts to buy and parts to print
Find a complete shopping'n'printing list including estimated prices for all modules and setups and also the RasPi and Hardware controlling parts in this [BILL OF MATERIALS](https://docs.google.com/spreadsheets/d/1U1MndGKRCs0LKE5W8VGreCv9DJbQVQv7O6kgLlB6ZmE/edit?usp=sharing)!

# Get Involved
This project is open so that anyone can get involved. You don't even have to learn CAD designing or programming. Find ways you can contribute in  [CONTRIBUTING](CONTRIBUTING.md)

## Credits
R. Heintzmann, X. Uwurukundo, H. Wang, N. Schramma, E. Bingoel, B. Marsikova, B. Diederich, Lichtwerkstatt, IPHT Jena
