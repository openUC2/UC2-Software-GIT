#include <Adafruit_GFX.h>
#include <Adafruit_NeoMatrix.h>
#include <Adafruit_NeoPixel.h>
#define PIN 2

Adafruit_NeoMatrix matrix = Adafruit_NeoMatrix(8, 8, PIN,
  NEO_MATRIX_TOP     + NEO_MATRIX_RIGHT +
  NEO_MATRIX_COLUMNS + NEO_MATRIX_PROGRESSIVE,
  NEO_GRB            + NEO_KHZ800);

void uc2wait(int period){
  unsigned long time_now = millis();  
  while(millis() < time_now + period){
      //wait approx. [period] ms
  };
}

void setup() {
  // put your setup code here, to run once:

  matrix.begin();
  matrix.setBrightness(255);
  matrix.fillRect(4, 5, 5, 6, matrix.Color(255, 255, 255));//matrix.fillScreen(matrix.Color(255,255,255));
  matrix.show();
  //uc2wait(1500);
  //matrix.fillScreen(0);
  //matrix.show();
}

void loop() {
  // put your main code here, to run repeatedly:

}
