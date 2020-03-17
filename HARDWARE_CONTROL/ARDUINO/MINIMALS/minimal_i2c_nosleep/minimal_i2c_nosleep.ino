#include <Arduino.h>
#include <WSWire.h>
#include <string.h>
#include <StepMotor.h>
#include "Adafruit_GFX.h"
#include "Adafruit_NeoMatrix.h"
#include "Adafruit_NeoPixel.h"
#include <SPI.h>

#define SLAVE_ADDRESS 0x07
#define CLOCK_FREQUENCY 100000 //choose according to frequency of I2C-Master
#define HEARTBEAT_INTERVAL 300000
#define LED 13
#define LEDARR_PIN 4
#define MAX_MSG_LEN 32
#define MAX_INST 10

typedef int(*callback)(int, int);

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

//Device Identifier
const char *DEVICE_ID = "LEDARR";

const int nCommands = 11;
const char *COMMANDSET[nCommands] = {"NA", "PXL", "HLINE", "VLINE", "RECT", "CIRC", "LEFT", "RIGHT", "TOP", "BOTTOM", "CLEAR"};
const char *INSTRUCTS[nCommands] = {"1", "4", "4", "4", "8", "6", "4", "4", "4", "4", "0"};

const int nComCMDs = 4;
const char *COM_CMDS[nComCMDs] = {"STATUS", "LOGOFF", "NAME"};

char busy_msg[7];

char receiveBuffer[MAX_MSG_LEN];
char sendBuffer[MAX_MSG_LEN];

char CMD[MAX_MSG_LEN];
int INST[MAX_INST];
char instBuffer[MAX_INST];

const size_t max_msg_size = sizeof(sendBuffer);

//flag to escape Wire-library callback-function (less error-prone)
volatile boolean receiveFlag = false;

//custom flags
bool registered = false;
volatile bool busy = false;

//Arduino devices
// StepMotor stepperX = StepMotor(12, 13, 2, 3);
// StepMotor stepperY = StepMotor(8, 9, 10, 11);
// StepMotor stepperZ = StepMotor(4, 5, 6, 7);
Adafruit_NeoMatrix matrix = Adafruit_NeoMatrix(8, 8, LEDARR_PIN, 
    NEO_MATRIX_TOP + NEO_MATRIX_RIGHT + NEO_MATRIX_COLUMNS + 
    NEO_MATRIX_PROGRESSIVE, NEO_GRB + NEO_KHZ800);

const int nrows = 8;
const int ncols = 8;
int ledNA = 4;

struct RGB {
  byte r;
  byte g;
  byte b;
};

struct RGB rgb;

//look up specific task to according user-defined command
void executeCommand(int nINST)
{
  if (strcmp(CMD, COM_CMDS[0]) == 0)
  { 
    const char *response = registered ? "registered" : "not registered";
    strlcat(sendBuffer, response, max_msg_size);
  }
  else if (strcmp(CMD, COM_CMDS[1]) == 0)
  {
    strlcat(sendBuffer, "Received LOGOFF.", max_msg_size);
    registered = false;
  }
  else if (strcmp(CMD, COM_CMDS[2]) == 0)
  {
    strlcat(sendBuffer, DEVICE_ID, max_msg_size);
  }
  //User-defined commands
  else if (strcmp(CMD, COMMANDSET[0]) == 0)
  {
    setNA(INST[0]);
  }
  else if (strcmp(CMD, COMMANDSET[1]) == 0)
  {
    strlcat(sendBuffer, "Pressed PXL", max_msg_size);
    int xpos = INST[0] % ncols;
    int ypos = INST[0] / ncols;
    updateColor(INST[nINST-3], INST[nINST-2], INST[nINST-1]);
    matrix.drawPixel(xpos, ypos, matrix.Color(rgb.r, rgb.g, rgb.b));
    matrix.show();
  }
  else if (strcmp(CMD, COMMANDSET[2]) == 0)
  {
    updateColor(INST[nINST-3], INST[nINST-2], INST[nINST-1]);
    drawRow(INST[0]);
  }
  else if (strcmp(CMD, COMMANDSET[3]) == 0)
  {
    updateColor(INST[nINST-3], INST[nINST-2], INST[nINST-1]);
    drawCol(INST[0]);
  }
  else if (strcmp(CMD, COMMANDSET[4]) == 0)
  {
    strlcat(sendBuffer, "Pressed RECT", max_msg_size);
    updateColor(INST[nINST-4], INST[nINST-3], INST[nINST-2]);
    bool fill = INST[nINST-1] != 0;
    drawRect(INST[0], INST[1], INST[2], INST[3], fill);
  }
  else if (strcmp(CMD, COMMANDSET[5]) == 0)
  {
    strlcat(sendBuffer, "Pressed CIRC", max_msg_size);
    updateColor(INST[nINST-3], INST[nINST-2], INST[nINST-1]);
    bool fill = INST[nINST-1] != 0;
    drawRect(INST[0], INST[1], INST[2], INST[3], fill);;
  }
  else if (strcmp(CMD, COMMANDSET[6]) == 0)
  {
    strlcat(sendBuffer, "Pressed LEFT", max_msg_size);
    drawRect(0, 0, 4, 8, true);
  }
  else if (strcmp(CMD, COMMANDSET[7]) == 0)
  {
    strlcat(sendBuffer, "Pressed RIGHT", max_msg_size);
    drawRect(4, 0, 4, 8, true);
  }
  else if (strcmp(CMD, COMMANDSET[8]) == 0)
  {
    strlcat(sendBuffer, "Pressed TOP", max_msg_size);
    drawRect(0, 0, 8, 4, true);
  }
  else if (strcmp(CMD, COMMANDSET[9]) == 0)
  {
    strlcat(sendBuffer, "Pressed BOTTOM", max_msg_size);
    drawRect(0, 4, 8, 4, true);
  }
  else if (strcmp(CMD, COMMANDSET[10]) == 0)
  {
    strlcat(sendBuffer, "Pressed CLEAR", max_msg_size);
    matrix.fillScreen(0);
    matrix.show();
  }
  else
  {
    strlcat(sendBuffer, "Command not found.", max_msg_size);
  }
}

void setup()
{
  pinMode(LED, OUTPUT);
  //Wire-library callbacks
  Wire.begin(SLAVE_ADDRESS);
  //Wire.setClock(CLOCK_FREQUENCY);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);

  matrix.begin();
  matrix.setBrightness(125);
  matrix.setTextColor(matrix.Color(255, 255, 255));
  matrix.setTextWrap(false);

  memset(receiveBuffer, 0, max_msg_size);
  memset(sendBuffer, 0, max_msg_size);

  delim_strt_len = (int)strlen(delim_strt);
  delim_stop_len = (int)strlen(delim_stop);
  delim_tbc_len = (int)strlen(delim_tbc);

  strlcat(busy_msg, delim_strt, sizeof(busy_msg));
  strlcat(busy_msg, "BUSY", sizeof(busy_msg));
  strlcat(busy_msg, delim_stop, sizeof(busy_msg));
}

void loop()
{
  if(receiveFlag)
  {
    busy = true;
    refresh_sendBuffer();
    int nINST = separateCommand();
    executeCommand(nINST);
    cleanUpReceive();
    busy = false;
    receiveFlag = false;
  }
}

//request callback of Wire-library
void requestEvent()
{
  if(!busy)
  {
    strlcat(sendBuffer, delim_stop, max_msg_size);
    Wire.write(sendBuffer);
    refresh_sendBuffer();
  }
  else
  {
    Wire.write(busy_msg);
  }
}

//receive callback for incoming data of Wire-library
void receiveEvent(int byteCount)
{
  Wire.readBytes(receiveBuffer, byteCount);
  receiveFlag = byteCount > 1;
}

void cleanUpReceive()
{
  memset(CMD, 0, max_msg_size);
  memset(INST, 0, 10);
  memset(receiveBuffer, 0, max_msg_size);
}
void cleanUpRequest()
{
  memset(sendBuffer, 0, max_msg_size);
}

int separateCommand()
{
  int count = 0;
  ptr_strt = strstr(receiveBuffer, delim_strt);
  ptr_stop = strstr(receiveBuffer, delim_stop);
  if ((ptr_strt != NULL) && (ptr_stop != NULL))
  {
    int len = ptr_stop - ptr_strt - 1;
    memcpy(CMD, ptr_strt + 1, len);
    CMD[len] = '\0';
    
    char *ptr_inst = NULL;
    ptr_inst = strstr(receiveBuffer, delim_inst);

    if(ptr_inst != NULL)
    {
      len = ptr_inst - ptr_strt - 1;
      CMD[len] = '\0';
      
      while(ptr_inst != ptr_stop)
      {
        ptr_strt = ptr_inst;
        ptr_inst = strstr(ptr_strt+1, delim_inst);
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

void refresh_sendBuffer()
{
  memset(sendBuffer, 0, max_msg_size);
  strlcat(sendBuffer, delim_strt, max_msg_size);
}

void drawRow(int y)
{
  int offset = (ncols - ledNA*2) * 0.5;
  if(y > offset && y < nrows-offset)
  {
    matrix.drawFastHLine(offset, y, ncols-offset*2, matrix.Color(rgb.r, rgb.g, rgb.b));
    matrix.show();
    strlcat(sendBuffer, "HLINE drawn", max_msg_size);
  }
  else
  {
    strlcat(sendBuffer, "Row is outside of NA", max_msg_size);
  }
}
void drawCol(int x)
{
  int offset = (nrows - ledNA * 2) * 0.5;
  if(x > offset && x < ncols-offset)
  {
    matrix.drawFastVLine(x, offset, nrows - offset * 2, matrix.Color(rgb.r, rgb.g, rgb.b));
    matrix.show();
    strlcat(sendBuffer, "VLINE drawn", max_msg_size);
  }
  else
  {
    strlcat(sendBuffer, "Column is outside of NA", max_msg_size);
  }
}
void drawRect(int x, int y, int w, int h, bool fill)
{
  if(fill){ 
    matrix.fillRect(x, y, w, h, matrix.Color(255, 255, 255));
  }
  else{
    matrix.drawRect(x, y, w, h, matrix.Color(255, 255, 255));
  }

  matrix.show();
}

void drawCirc(int x, int y, int w, int h)
{
  matrix.drawCircle(x, y, ledNA, matrix.Color(rgb.r, rgb.g, rgb.b));
}

void setNA(int select)
{
	if (select > 4)
	{
		select = 4;
	}
	if (select < 1)
	{
    select = 1;
		matrix.fillScreen(0);
	}
	ledNA = select;
  char msg[3];
  sprintf(msg, "%d", select);
  strlcat(sendBuffer, "NA set to ", max_msg_size);
  strlcat(sendBuffer, msg, max_msg_size);
}

void updateColor(uint8_t r, uint8_t g, uint8_t b)
{
  rgb.r = r;
  rgb.g = g;
  rgb.b = b;
}