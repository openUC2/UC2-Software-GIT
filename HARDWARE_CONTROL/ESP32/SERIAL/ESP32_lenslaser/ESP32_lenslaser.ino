#include <Stepper.h>
#include <String.h>

#ifdef __AVR__
#include <avr/power.h> // Required for 16 MHz Adafruit Trinket
#endif

#define CLOCK_FREQUENCY 100000 //choose according to frequency of I2C-Master
#define HEARTBEAT_INTERVAL 300000
#define LED 13
#define BF_PIN 0
#define FLUO_PIN 1
#define LEDARR_PIN 13
#define MAX_MSG_LEN 32
#define MAX_INST 10


/*
   Simple SERIAL Interface for basic functionalities on the ESP32 with "Microscope" from micron oxford

   COMMANDS:
   They have to be declared in the varialbe:
   const char *COMMANDSET (remember to update the ncommands accordingly)

   ACTUATORS
   NAME      | Value
   -- DRVX   | 0..1000
   -- DRVY   | 0..1000
   -- DRVZ   | 0..1000
   -- LENS1X | 0..32768
   -- LENS1Y | 0..32768
   -- LENS2X | 0..32768
   -- LENS2Y | 0..32768

   LIGHT
   -- LAS1 | 0..32768
   -- LAS2 | 0..32768
   -- LED1 | 0..1



   COMMAND EXAMPLES:
   Constructing a command send by a serial device (e.g. pyerial)
   has to contain the starting/stopping delimeter *xxx+xxx#.
   Commands are concatenated using the + .

   Drive motor 1000 steps in x-direction:
 * *DRVX+1000#

   Drive motor -100 steps in Z-direction:
 * *DRVZ+-1000#

   Move Lens1 X to position 100:
 * *LENS1X+100#
*/
const char *CMD_DRVX =    "DRVX";
const char *CMD_DRVY =   "DRVX";
const char *CMD_DRVZ =   "DRVZ";
const char *CMD_LENS1X =  "LENS1X";
const char *CMD_LENS1Z =  "LENS1Z";
const char *CMD_LENS2X =  "LENS2X";
const char *CMD_LENS2Z =  "LENS2Z";
const char *CMD_LAS1 =    "LAS1";
const char *CMD_LAS2 =    "LAS2";
const char *CMD_LED1 =    "LED1";
const char *CMD_LX_SOFI =  "LX_SOFI";
const char *CMD_LZ_SOFI =  "LZ_SOFI";
const char *CMD_LX_SOFI_A =  "LX_SOFI_A";
const char *CMD_LZ_SOFI_A =  "LZ_SOFI_A";

typedef int (*callback)(int, int);

const char *delim_strt = "*";
const char *delim_stop = "#";
const char *delim_cmds = ";";
const char *delim_inst = "+";
const char *delim_tbc = "...";
int delim_strt_len;
int delim_stop_len;
int delim_tbc_len;
char *ptr_strt = NULL;
char *ptr_stop = NULL;

/*void run_X(int nsteps);
  void run_Y(int nsteps);
  void run_Z(int nsteps);*/
void shiftOutBuffer(int);
int separateCommand();
void cleanUpReceive();
void cleanUpReceive();
void cleanUpRequest();


//User-defined commands
char msg[7];

int FLUO_STATUS = 0;

// Unique Device Identifier
const char *DEVICE_ID = "cellstorm";


/*
    Declare pins for connecting the hardware:
*/

// LASER
int LASER_PIN_PLUS = 23;// 22;
int LASER_PIN_MINUS = 34;//23;
int LASER2_PIN_PLUS = 19;// 22;
int LASER2_PIN_MINUS = 33;//23;

// LENS
int LENS_X_PIN = 26;
int LENS_Z_PIN = 25;

// LED
int LED_PIN = 2;

// MOTOR
const int stepsPerRevolution = 2048;
Stepper motor_z = Stepper(stepsPerRevolution, 21, 17, 4, 16);
unsigned int motor_speed = 8;
int STEPS = 200;


/*
    Configure hardware variables
*/

// global switch for vibrating the lenses
int sofi_periode = 100;  // ms
int sofi_amplitude_x = 0;   // how many steps +/- ?
int sofi_amplitude_z = 0;   // how many steps +/- ?

// default values for x/z lens' positions
int lens_x_int = 0;
int lens_z_int = 0;
int laser_int = 0;
int laser2_int = 0;
int lens_x_offset = 0;
int lens_z_offset = 0;//1000;

boolean is_sofi_x = false;
boolean is_sofi_z = false;


// PWM Stuff
int pwm_resolution = 15;
int pwm_frequency = 800000;//19000; //12000

// lens x-channel
int PWM_CHANNEL_X = 0;

// lens z-channel
int PWM_CHANNEL_Z = 1;

// laser-channel
int PWM_CHANNEL_LASER = 2;

// laser-channel
int PWM_CHANNEL_LASER_2 = 3;



/*
   Don't change this part
*/

// Reporting flags for serial communication
const int nComCMDs = 3;
const char *COM_CMDS[nComCMDs] = {"STATUS", "LOGOFF", "NAME"};

// Allocate memory
char busy_msg[7];

char receiveBuffer[MAX_MSG_LEN];
char sendBuffer[MAX_MSG_LEN];

char CMD[MAX_MSG_LEN];      // Commands
int INST[MAX_INST];         // Instructions (i.e. nubmers)
char instBuffer[MAX_INST];  // INStruction buffer

const int outBufLen = MAX_MSG_LEN * 4;
char outBuffer[outBufLen];

const size_t max_msg_size = sizeof(sendBuffer);

//flag to escape Wire-library callback-function (less error-prone)
volatile boolean receiveFlag = false;

//custom flags
bool registered = false;
volatile bool busy = false;





void setup()
{
  Serial.begin(115200);
  Serial.println("Starting the programm here..");

  /*
      Setup Hardware
  */
  /* set led and laser as output to control led on-off */
  pinMode(LED_PIN, OUTPUT);

  // switch of the laser directly
  pinMode(LASER_PIN_MINUS, OUTPUT);
  pinMode(LASER_PIN_MINUS, OUTPUT);
  digitalWrite(LASER_PIN_PLUS, LOW);
  digitalWrite(LASER_PIN_MINUS, LOW);
  digitalWrite(LASER2_PIN_PLUS, LOW);
  digitalWrite(LASER2_PIN_MINUS, LOW);

  // Visualize, that ESP is on!
  digitalWrite(LED_PIN, HIGH);
  delay(1000);
  digitalWrite(LED_PIN, LOW);

  /* setup the PWM ports and reset them to 0*/
  ledcSetup(PWM_CHANNEL_X, pwm_frequency, pwm_resolution);
  ledcAttachPin(LENS_X_PIN, PWM_CHANNEL_X);
  ledcWrite(PWM_CHANNEL_X, 0);

  ledcSetup(PWM_CHANNEL_Z, pwm_frequency, pwm_resolution);
  ledcAttachPin(LENS_Z_PIN, PWM_CHANNEL_Z);
  ledcWrite(PWM_CHANNEL_Z, 0);

  ledcSetup(PWM_CHANNEL_LASER, pwm_frequency, pwm_resolution);
  ledcAttachPin(LASER_PIN_PLUS, PWM_CHANNEL_LASER);
  ledcWrite(PWM_CHANNEL_LASER, 0);

  ledcSetup(PWM_CHANNEL_LASER_2, pwm_frequency, pwm_resolution);
  ledcAttachPin(LASER2_PIN_PLUS, PWM_CHANNEL_LASER_2);
  ledcWrite(PWM_CHANNEL_LASER_2, 0);


  // Set the speed of the motor:
  motor_z.setSpeed(motor_speed);
  // Set the speed to 5 rpm:
  motor_z.step(50);
  motor_z.step(-50);

  // test lenses
  ledcWrite(PWM_CHANNEL_Z, 5000);
  ledcWrite(PWM_CHANNEL_X, 5000);
  delay(500);

  //Set the lenses to their offset level
  ledcWrite(PWM_CHANNEL_Z, lens_z_offset);
  ledcWrite(PWM_CHANNEL_X, lens_x_offset);



  /*
     Handle deconding stuff
  */
  memset(receiveBuffer, 0, max_msg_size);
  memset(sendBuffer, 0, max_msg_size);
  memset(outBuffer, 0, sizeof(outBuffer));

  delim_strt_len = (int)strlen(delim_strt);
  delim_stop_len = (int)strlen(delim_stop);
  delim_tbc_len = (int)strlen(delim_tbc);
  strlcat(busy_msg, delim_strt, sizeof(busy_msg));
  strlcat(busy_msg, "BUSY", sizeof(busy_msg));
  strlcat(busy_msg, delim_stop, sizeof(busy_msg));

}

void loop()
{
  //delayMicroseconds(1); // make the watchdog happy
  int availableBytes = Serial.available();

  if (availableBytes and not busy) {
    for (int i = 0; i < availableBytes; i++)
    {
      receiveBuffer[i] = Serial.read();
    }
    busy = true;
    int nINST = separateCommand();
    executeCommand(nINST);
    cleanUpReceive();
    busy = false;
    receiveFlag = false;
  }
}




//look up specific task to according user-defined command
void executeCommand(int nINST)
{
  Serial.println(CMD);
  Serial.println(nINST);
  Serial.println((int)(INST[0]));

  /*
      Get back status parameters - for later use
  */
  if (strcmp(CMD, COM_CMDS[0]) == 0)
  {
    const char *response = registered ? "registered" : "not registered";
    strlcat(outBuffer, response, outBufLen);
    Serial.println(response);
  }
  else if (strcmp(CMD, COM_CMDS[1]) == 0)
  {
    strlcat(outBuffer, "Received LOGOFF.", outBufLen);
    registered = false;
    Serial.println("Received LOGOFF.");
  }
  else if (strcmp(CMD, COM_CMDS[2]) == 0)
  {
    strlcat(outBuffer, DEVICE_ID, outBufLen);
    Serial.println(DEVICE_ID);
  }



  // Convert the command value to something useful
  int payload = (int)(INST[0]);
  Serial.print("Payload: ");
  Serial.println(payload);
  // Turn on/off LED
  if (strcmp(CMD, CMD_LED1) == 0)  {
    /* we got '1' -> on */
    if (payload == 1) {
      digitalWrite(LED_PIN, HIGH);
    } else {
      /* we got '0' -> on */
      digitalWrite(LED_PIN, LOW);
    }
  }

  /*
      Handle lens vibration for SOFI in X
  */
  if (strcmp(CMD, CMD_LX_SOFI) == 0)   {
    /* we got '1' -> on */
    if (payload == 0) {
      is_sofi_x = false;
      sofi_amplitude_x = 0;
    } else {
      is_sofi_x = true;
      sofi_amplitude_x = abs((int)payload);
      Serial.print("Sofi AMplitude X set to: ");
      Serial.print(sofi_amplitude_x);
      Serial.println();
    }
  }

  /*
      Handle lens vibration for SOFI in Z
  */
  if (strcmp(CMD, CMD_LZ_SOFI) == 0) {
    /* we got '1' -> on */
    if (payload == 0) {
      is_sofi_z = false;
      Serial.print("Sofi Z is swiched off!");
      sofi_amplitude_z = 0;
    } else {
      is_sofi_z = true;
      sofi_amplitude_z = abs(payload);
      sofi_amplitude_z = 500;
      Serial.print("Sofi Amplitude Z set to: ");
      Serial.print(sofi_amplitude_z);
      Serial.println();
    }
  }

  // Catch the value for movement of lens in X-direction (right)
  if (strcmp(CMD, CMD_LAS1) == 0) {
    laser_int = abs(payload);
    ledcWrite(PWM_CHANNEL_LASER, laser_int);
    Serial.print("Laser Intensity is set to: ");
    Serial.print(laser_int);
    Serial.println();
  }

  // Catch the value for movement of lens in X-direction (right)
  if (strcmp(CMD, CMD_LAS2) == 0)  {
    laser2_int = abs((int)payload);
    ledcWrite(PWM_CHANNEL_LASER_2, laser2_int);
    Serial.print("Laser Intensity is set to: ");
    Serial.print(laser2_int);
    Serial.println();
  }

  // Catch the value for movement of lens in X-direction (right)
  if (strcmp(CMD, CMD_LENS1X) == 0)  {
    lens_x_int = abs(payload);
    ledcWrite(PWM_CHANNEL_X, lens_x_int + lens_x_offset);
    Serial.print("Lens (right) X is set to: ");
    Serial.print(lens_x_int);
    Serial.println();
  }

  // Catch the value for movement of lens in Z-direction (right)
  if (strcmp(CMD, CMD_LENS1Z) == 0)  {
    lens_z_int = abs(payload);
    ledcWrite(PWM_CHANNEL_Z, lens_z_int + lens_z_offset);
    Serial.print("Lens (right) Y is set to: ");
    Serial.print(lens_z_int);
    Serial.println();
  }


  // Catch the value for stepment of lens in X-direction
  if (strcmp(CMD, CMD_DRVZ) == 0)  {
    // Drive motor X in positive direction
    int mysteps = payload;
    motor_z.step(mysteps);
    Serial.print("Motor is running in x for: ");
    Serial.print(mysteps);
    Serial.println();
  }

  /*
    if (String(CMD) == LED_ARRAY_TOPIC)  {
     //we got '1' -> on
      if (payload_int == 1) {
        ledson(strip.Color(255,   255,   255));
      } else {
        //we got '0' -> on
        ledson(strip.Color(0,   0,   0));
      }
    }
  */

}



void cleanUpReceive()
{
  memset(CMD, 0, max_msg_size);
  memset(INST, 0, 10);
  memset(receiveBuffer, 0, max_msg_size);
}
void cleanUpRequest()
{
  memset(outBuffer, 0, sizeof(outBuffer));
  memset(sendBuffer, 0, max_msg_size);
}

int separateCommand()
{
  int count = 0;
  Serial.println(receiveBuffer);
  ptr_strt = strstr(receiveBuffer, delim_strt);
  ptr_stop = strstr(receiveBuffer, delim_stop);
  if ((ptr_strt != NULL) && (ptr_stop != NULL))
  {
    int len = ptr_stop - ptr_strt - 1;
    memcpy(CMD, ptr_strt + 1, len);
    CMD[len] = '\0';

    char *ptr_inst = NULL;
    ptr_inst = strstr(receiveBuffer, delim_inst);

    if (ptr_inst != NULL)
    {
      len = ptr_inst - ptr_strt - 1;
      CMD[len] = '\0';

      while (ptr_inst != ptr_stop)
      {
        ptr_strt = ptr_inst;
        ptr_inst = strstr(ptr_strt + 1, delim_inst);
        if (!ptr_inst)
          ptr_inst = ptr_stop;
        len = ptr_inst - ptr_strt - 1;
        if (len < MAX_INST)
        {
          memcpy(instBuffer, ptr_strt + 1, len);
          instBuffer[len] = '\0';
          INST[count] = atoi(instBuffer);
        }
        count++;
      }
    }
  }
  return count;
}


int numberOfSends()
{
  int offset = delim_strt_len + delim_stop_len;
  int n = (int)strlen(outBuffer) / (MAX_MSG_LEN - offset);
  return n + 1;
}

void prepareSend()
{
  int n = numberOfSends();
  strlcat(sendBuffer, delim_strt, MAX_MSG_LEN);
  if (n > 1)
  {
    int bound = MAX_MSG_LEN - delim_strt_len - delim_tbc_len;
    strlcat(sendBuffer, outBuffer, bound);
    strlcat(sendBuffer, delim_tbc, MAX_MSG_LEN);
    shiftOutBuffer(bound - delim_strt_len - 1);
  }
  else
  {
    strlcat(sendBuffer, outBuffer, MAX_MSG_LEN);
    memset(outBuffer, 0, outBufLen);
  }
  strlcat(sendBuffer, delim_stop, MAX_MSG_LEN);
}

void shiftOutBuffer(int shiftLength)
{
  if (shiftLength >= (int)strlen(outBuffer))
  {
    memset(outBuffer, 0, sizeof(outBuffer));
  }
  else
  {
    for (int i = 0; i < (outBufLen - shiftLength); i++)
    {
      outBuffer[i] = outBuffer[i + shiftLength];
    }
  }
}

int countInstructions()
{
  int n = 10;
  int count;
  char *p = receiveBuffer;
  for (count = 0; count <= n; count++)
  {
    p = strstr(p, delim_inst);
    if (!p)
      break;
    p++;
  }
  return count;
}
