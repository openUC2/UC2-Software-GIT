# ESP32
This is the Guide to explain how to use and control the ESP32 for controlling Motors or LEDs.  

<p align="center">
<img src="./IMAGES/Control_MQTT_system.jpg" width="800">
</p>

Our general principle behind will be explained soon. For now, let's focus on how to setup devices. 

## Our tested ESP32 family
*   [ESP32 Wemos mini]()
*   [ESP32 nodeMCU]()
*   [ESP32 devKITv1]()

## Our MQTT-command scheme
Will be explained soon. :)

## Setting up the IDE
The ESP32 is a mircocontroller that has many functional units (chips/routines), a real second thread (core) as well as an enhanced RAM as compared to the ARDUINO. Hence, it is way more powerful. Still, there is no possibility to store data/variables generated on runtime for longer than the runtime. Hence, we flash the device initially and then keep the inserted parameters and code. Once environmental parameters (e.g. IP-adresses or Topic-names) change, we have to change the code and flash the device again. For flashing, you can choose between multiple IDEs. While we chose to work with [VSCode](https://code.visualstudio.com/) and [PlatformIO](https://docs.platformio.org/en/latest/integration/ide/vscode.html) we belief that the ARDUINO IDE is a solid environment for starters.
*   Download and install the [ARDUINO-IDE as described here](https://www.arduino.cc/en/Guide/windows)
*   Prepare your IDE to work with the ESP32 boards, as [awesomly described here](https://randomnerdtutorials.com/installing-the-esp32-board-in-arduino-ide-windows-instructions/)
*   Let's assume your IDE is setup as default, hence your standard library PATH will be `%HOME%\Documents\Arduino\libraries\` and your presets in the IDE should look like this: 
    <p align="center">
    <img src="./IMAGES/arduinoidePATH.png" width="800">
    </p>
Now, we need to add the libraries necessary to compile and flash our Scripts onto ESP32. 
*   [As described here](https://www.arduino.cc/en/Guide/Libraries) go to `Include Library -> Manage Libraries` and install the following packages: 
    *   Adafruit_GFX
    *   Adafruit_NeoMatrix
    *   Adafruit_NeoPixel
*   Download the [PubSubClient-Package from here](https://github.com/knolleary/pubsubclient/), unzip, rename to `pubsubclient` and copy into your `Arduino/library` folder as before or [explained here](https://randomnerdtutorials.com/esp32-mqtt-publish-subscribe-arduino-ide/)
*   The WSWire-Library can be found [here](https://github.com/steamfire/WSWireLib)

You can find a tested version (with our code) of the packages as well as our StepMotor-Library under [ARDUINO/LIBRARIES](../ARDUINO/LIBRARIES/) except for PubSubClient, which can be found in the [ESP32/LIBRARIES](./LIBRARIES) folder.

## Getting MQTT properties
If you followed [our guide how to setup a new RasPi with our GUI](../../GUI/RASPBERRY_PI/README.md) from scratch or if you already have a mosquitto (MQTT-protocol) server running on the Raspberry, we now need to know the IP-adress of the MQTT-server host (in this case = IP of RasPi). In a terminal (on the Raspi) enter: 
```
$ ifconfig wlan0 | grep -w inet
```
<p align="center">
<img src="./IMAGES/mqtt01m.png" width="400" alt="">
</p> 

In our case the IP is: `192.168.178.160`. Now it depends which device you cant to connect. The available devices are: 
*   [LED-array](./GENERAL/ESP32_ledarr)
*   [minimal LED-array ](./GENERAL/ESP32_ledarr_minimal_with_Button) (minimal working example together with a button)
*   [MOTOR and Fluorescence (all-in-one) module](./GENERAL/ESP32_motor_fluo)

[Learn how to prepare the code, flash it onto the ESP32 and run the device here](./GENERAL/README.md). 

## Credits
R. Heintzmann, X. Uwurukundo, H. Wang, B. Marsikova, B. Diederich, Lichtwerkstatt, IPHT Jena