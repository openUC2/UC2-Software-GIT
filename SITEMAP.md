# Site map for easy navigation

## For more information about the project in general and for all the hardware visit our [main repository](https://github.com/bionanoimaging/UC2-GIT)

## [Main page with the 'Getting started'](./Readme.md)

There you also find our

* [Code of conduct](./CODE_OF_CONDUCT.md)
* [Contributor guidelines](./CONTRIBUTING.md)


 ## [GUI](./GUI)

 [HERE](./GUI) you find our graphical user interface for both
 * [Raspberry Pi](./GUI/RASPBERRY_PI)
    * [RASPIapp_py3](./GUI/RASPBERRY_PI/RASPIapp_py3) - current version of the GUI
    * [RASPIapp_py27](./GUI/RASPBERRY_PI/RASPIapp_py27) - older version of the GUI
    * [Scripts](./GUI/RASPBERRY_PI/SCRIPTS) - useful scripts like the [FIX_date](./GUI/RASPBERRY_PI/SCRIPTS/FIX_date) and some GUI installation prerequisites
 * as an [Android App](./GUI/Android)
    * [UC2-basic](./GUI/Android/UC2-basic) - older version
    * [UC2-TheBox](./GUI/Android/UC2-TheBox) - up-to-date version


 ## [Hardware Controlling](./HARDWARE_CONTROL)

 [HERE](./HARDWARE_CONTROL) you find the code and other necessary information to control the motors and illumination using  
 * [Arduino (and alike) via I2C (Hardwired)](./HARDWARE_CONTROL/ARDUINO)
    * [GENERAL folder](./HARDWARE_CONTROL/ARDUINO/GENERAL) where you find the code for LED array, Motors and Motor with Fluo-mode
    * [Libraries](./HARDWARE_CONTROL/ARDUINO/libraries) that you will need
    * [MINIMALS folder](./HARDWARE_CONTROL/ARDUINO/MINIMALS) with some example code, mostly for testing the hardware
 * [ESP32 (and alike) via MQTT (WiFI)](./HARDWARE_CONTROL/ESP32)
    * [GENERAL folder](./HARDWARE_CONTROL/ESP32/GENERAL) where you find the code for LED array, Motors and Motor with Fluo-mode
    * [forANDROID folder](./HARDWARE_CONTROL/ESP32/forANDROID) where you find the code for LED array, Motors and Motor with Fluo-mode that works with the Android App
    * [Libraries](./HARDWARE_CONTROL/ESP32/LIBRARIES) that you will need


 ## [Processing](./PROCESSING)

 [HERE](./PROCESSING) you find the toolbox used for data-processing of the Macrophage and MDCK video in the [publication](https://www.biorxiv.org/content/10.1101/2020.03.02.973073v1) - "UC2 – A Versatile and Customizable low-cost 3D-printed Optical Open-Standard for microscopic imaging"


 ## [Workshops](./WORKSHOPS)

 [HERE](./WORKSHOPS) you find the relevant software from some of the workshops we organised. Find out more about our workshops in the dedicated section of the [main repository](https://github.com/bionanoimaging/UC2-GIT/tree/master/WORKSHOP)
