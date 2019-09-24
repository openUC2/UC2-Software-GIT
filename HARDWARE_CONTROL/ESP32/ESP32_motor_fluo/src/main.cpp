// ----------- ----------- ----------- ----------- ----------- -----------
// ESP32 script to accept MQTT commands for UC2-control
// by: Rene Lachmann
// date: 11.09.2019
// based on Arduino-Interface by Rene Lachmann, Xavier Uwurukundu
//----------- ----------- ----------- ----------- ----------- -----------

// ----------------------------------------------------------------------------------------------------------------
//                          INCLUDES
#include <WiFi.h>
#include <PubSubClient.h>
#include <string.h>
#include <vector>
#include <StepMotor.h>
#include "driver/ledc.h"
// ----------------------------------------------------------------------------------------------------------------
//                          Global Defines
#define MAX_CMD 3
#define MAX_INST 10
#define NCOMMANDS 15
#define MAX_MSG_LEN 40
#define LED_BUILTIN 11
#define LED_FLUO_PIN 26

// ----------------------------------------------------------------------------------------------------------------
//                          Parameters
// ~~~~ Device ~~~~
const char *deviceData = "ESP32-MOT1 on Setup 1.";

// ~~~~  Wifi  ~~~~
const char *ssid = "GUEST_JRC";
const char *password = "HHMI@Newton";
WiFiClient espClient;
PubSubClient client(espClient);

// ~~~~  MQTT  ~~~~
const char *MQTT_SERVER = "10.9.2.116";
const char *MQTT_CLIENTID = "S1_MOT2_ESP32"; //"S1_MOT2_ESP32"
const char *MQTT_USER = "ESP32";
const char *MQTT_PASS = "23SPE";
const int MQTT_SUBS_QOS = 0;
const unsigned long period = 80000; // 80s
unsigned long time_now = 0;
// topics to listen/publish to
const char *topicREC = "/S1/MOT2/REC";
const char *topicSTATUS = "/S1/MOT2/STATUS";
const char *topicANNOUNCE = "/S1/MOT2/ANNOUNCE";
const char *delim_inst = "+";
const int delim_len = 1;

// ~~~~ MOTOR ~~~~
StepMotor stepperZ = StepMotor(27, 25, 32, 4);
StepMotor stepperY = StepMotor(10, 12, 11, 13);
StepMotor stepperX = StepMotor(27, 25, 32, 4); // never connected to same ESP32 as stepperZ -> hence: universally possible

// ~~~~ FLUO ~~~~
int led_fluo_pwm_frequency = 12000;
int led_fluo_pwm_channel = 0;
int led_fluo_pwm_resolution = 8;

// ~~~~ Commands ~~~~
const char *CMD;     //Commands like: PXL -> limited to size of 3?
int *INST[MAX_INST]; //Maximum number of possible instructions =
std::vector<int> INSTS;
std::string CMDS;

const char *COMMANDSET[NCOMMANDS] = {"DRVX", "DRVY", "DRVZ", "FLUO"};
const char *INSTRUCTS[NCOMMANDS] = {"1", "1", "1", "1"};

// ~~~~ FLUO ~~~~
int FLUO_STATUS = 0;
// ----------------------------------------------------------------------------------------------------------------
//                          Additional Functions
void uc2wait(int period)
{
    unsigned long time_now = millis();
    while (millis() < time_now + period)
    {
        //wait approx. [period] ms
    };
}
void setup_wifi()
{
    uc2wait(10);
    // We start by connecting to a WiFi network
    Serial.println();
    Serial.print("Device-MAC: ");
    Serial.println(WiFi.macAddress());
    Serial.print("Connecting to ");
    Serial.print(ssid);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED)
    {
        uc2wait(500);
        Serial.print(".");
    }

    Serial.println("");
    Serial.print("WiFi connected to IP:");
    Serial.println(WiFi.localIP());
}

int separateMessage(byte *message, unsigned int length)
{

    Serial.println("Seperating Message.");
    Serial.print("Message=");
    char messageSep[length];
    for (int myc = 0; myc < length; myc++)
    {
        messageSep[myc] = (char)message[myc];
        Serial.print(messageSep[myc]);
    }
    messageSep[length] = NULL;
    Serial.println("");
    Serial.print("Mess=");
    std::string mess(messageSep);
    Serial.println(mess.c_str());
    size_t pos = 0;
    int i = 0;
    bool found_cmd = false;
    while ((pos = mess.find(delim_inst)) != std::string::npos)
    {
        if (!found_cmd)
        {
            Serial.print("CMD-del@");
            Serial.println(pos);
            CMDS = mess.substr(0, pos);
            Serial.print("CMDS=");
            CMD = CMDS.c_str();
            Serial.println(CMD);
            found_cmd = true;
        }
        else
        {
            INSTS.push_back(atoi(mess.substr(0, pos).c_str()));
            Serial.print("INST[");
            Serial.print(i);
            Serial.print("]=");
            Serial.println(INSTS[i]);
            i++;
        }
        mess.erase(0, pos + delim_len);
    }
    if (!found_cmd)
    {
        Serial.print("CMD-del@");
        Serial.println(pos);
        CMDS = mess.substr(0, pos);
        Serial.print("CMDS=");
        CMD = CMDS.c_str();
        Serial.println(CMD);
        found_cmd = true;
    }
    else if (mess.length() > 0)
    {
        INSTS.push_back(atoi(mess.substr(0, pos).c_str()));
        Serial.print("INST[");
        Serial.print(i);
        Serial.print("]=");
        Serial.println(INSTS[i]);
        i++;
    }
    else
    {
        Serial.println("Nothing found...");
    }
    return i;
    mess.clear();
}

void callback(char *topic, byte *message, unsigned int length)
{
    Serial.println("Callback-func called.");
    // test topics
    if (strcmp(topic, topicREC) == 0)
    {
        Serial.println(topicREC);
        int nINST = separateMessage(message, length);
        if (strcmp(CMD, COMMANDSET[0]) == 0)
        {
            stepperX.Move((int)(INSTS[0] * 10));
        }
        else if (strcmp(CMD, COMMANDSET[1]) == 0)
        {
            stepperY.Move((int)(INSTS[0] * 10));
        }
        else if (strcmp(CMD, COMMANDSET[2]) == 0)
        {
            stepperZ.Move(INSTS[0] * 10);
        }
        else if (strcmp(CMD, COMMANDSET[3]) == 0)
        {
            //analogWrite(FLUO_PIN, INSTS[0]);
            ledcWrite(led_fluo_pwm_channel, INSTS[0]);
        }
        else
        {
            Serial.print("CMD not found.");
        }
    }
    else if (strcmp(topic, topicSTATUS) == 0)
    {
        Serial.println(topicSTATUS);
    }
    else if (strcmp(topic, topicANNOUNCE) == 0)
    {
        Serial.println(topicANNOUNCE);
    }
    else
    {
        Serial.print("Assortion Error: Nothing found for topic=");
        Serial.println(topic);
    }
    INSTS.clear();
}

void reconnect()
{
    // Loop until we're reconnected
    while (!client.connected())
    {
        Serial.print("Attempting MQTT connection...");
        // Attempt to connect
        if (client.connect(MQTT_CLIENTID, topicSTATUS, 2, 1, "0"))
        {
            // client.connect(MQTT_CLIENTID,MQTT_USER,MQTT_PASS,"esp32/on",2,1,"off")
            Serial.println("connected");
            // Subscribe
            client.subscribe(topicREC);
            client.publish(topicSTATUS, "1");
            client.publish(topicANNOUNCE, deviceData);
        }
        else
        {
            Serial.print("failed, rc=");
            Serial.print(client.state());
            Serial.println(" try again in 5 seconds");
            // Wait 5 seconds before retrying
            uc2wait(5000);
        }
    }
}

// ----------------------------------------------------------------------------------------------------------------
//                          SETUP
void setup()
{
    Serial.begin(115200);
    // check for connected motors
    //status = bme.begin();
    setup_wifi();
    client.setServer(MQTT_SERVER, 1883);
    client.setCallback(callback);
    pinMode(LED_BUILTIN, OUTPUT);
    time_now = millis();
    //testCPP();
    //pinMode(LED_BUILTIN, OUTPUT);
    //pinMode(LED_FLUO_PIN, OUTPUT);
    ledcSetup(led_fluo_pwm_channel, led_fluo_pwm_frequency, led_fluo_pwm_resolution);
    ledcAttachPin(LED_FLUO_PIN, led_fluo_pwm_channel);
    ledcWrite(led_fluo_pwm_channel, 20); //analogWrite(FLUO_PIN, 20);
    uc2wait(1000);
    ledcWrite(led_fluo_pwm_channel, 0); //analogWrite(FLUO_PIN, 0,0);
    uc2wait(100);
    stepperX.SetSpeed(10);
    stepperY.SetSpeed(10);
    stepperZ.SetSpeed(10);
}
// ----------------------------------------------------------------------------------------------------------------
//                          LOOP
void loop()
{
    if (!client.connected())
    {
        reconnect();
    }
    client.loop();
    if (time_now + period < millis())
    {
        client.publish(topicSTATUS, "1");
        time_now = millis();
    }
}
// ----------------------------------------------------------------------------------------------------------------
