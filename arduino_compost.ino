#include <Wire.h>
#define SLAVE_ADDRESS 0x04 //address of Arduino via i2c connection

void setup() {
  Serial.begin(9600);
  Wire.begin(SLAVE_ADDRESS);
  Wire.onRequest(transmit);
}

void loop() {
//  transmit();
  delay(10);
}

//callback for sent data
void transmit(){
  int moisture_connect = 0;
  int temperature_connect = 0;
  int moisture = analogRead(A1);
  int moisture_adj = map(moisture, 0, 580, 0, 100);
  if ((moisture_adj >= 0) && (moisture_adj <= 120))
    moisture_connect = 1;
  if (moisture_adj >100)
    moisture_adj = 100;

  float temperature = float(analogRead(A0));
  float Rt = 10000.0 * temperature / (1024.0 - temperature);
  int temperature_adj = 1.0/(1/273.15 + 1/3435.0 * log(Rt/27700.0)) - 273.15;
  if ((temperature_adj >= 0) && (temperature_adj <= 100))
    temperature_connect = 1;
  if ((temperature_adj < 0) || (temperature_adj > 100))
    temperature_adj = 0;
    
  int val = (temperature_connect<<15) + (temperature_adj<<8) + (moisture_connect<<7) + moisture_adj;
  byte adc[] = {val & 0xff, (val >> 8) & 0xff};
  Wire.write(adc, sizeof(int));
  Serial.print("moisture:");
  Serial.print(moisture_adj);
  Serial.print("  temperature:");
  Serial.println(temperature_adj);
  delay(0.001);
}
