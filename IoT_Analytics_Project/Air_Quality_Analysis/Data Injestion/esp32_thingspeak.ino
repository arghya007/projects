#include <WiFiClientSecure.h>
#include "ThingSpeak.h"
#include <MQUnifiedsensor.h>
#include "DHT.h"


String hostname = "ESP32.MO135";

// Network Credentials
//const char* ssid = "Aarusha301";
//const char* pass = "ahpl@301";

const char* ssid = "sOuLkEePeR";
const char* pass = "asdf1234";

// Thingspeak channel details
unsigned long myChannelNumber = 2034104;
const char * myWriteAPIKey = "27P7TSLJU50ZQFMS";

//Definitions
#define placa "ESP-32"

//Led OnBoard
#define ONBOARD_LED  2

// Input Pins of the board
#define gas_sensor 32
#define noise_sensor 35
#define temp_hum_sensor 25

//Sensor type
#define type "MQ-135"
#define DHTTYPE DHT11 

//RS / R0 = 3.6 ppm
#define RatioMQ135CleanAir 3.6

// Voltage 5v
#define Voltage_Resolution 5

// For Arduino UNO/MEGA/NANO
#define ADC_Bit_Resolution 10

//Declare Sensor
MQUnifiedsensor MQ135(placa, Voltage_Resolution, ADC_Bit_Resolution, gas_sensor, type);
DHT dht(temp_hum_sensor, DHTTYPE);
WiFiClient  client;

void LED_Blink(int delayTime, int Replay){
  for (int i = 0; i <= Replay; i++) {
    delay(delayTime); digitalWrite(ONBOARD_LED,HIGH);
    delay(delayTime); digitalWrite(ONBOARD_LED,LOW);
	}
}

//Sensors Reading
String readMQ135CO() {
  // Sensor readings may also be up to 1 seconds
  // Read PPM CO concentration
  MQ135.setA(605.18); MQ135.setB(-3.937);
  float CO = MQ135.readSensor();
  // Check if any reads failed and exit early (to try again).
  if (isnan(CO)) {    
    Serial.println("CO PPP : Failed From Sensor!");
    return "--";
  }
  else {
    Serial.print("CO: ");
    Serial.println(CO);
    ThingSpeak.setField(1, CO);
    return String(CO);
  }
}

String readMQ135CO2() {
  // Sensor readings may also be up to 1 seconds
  // Read PPM CO2 concentration
  MQ135.setA(110.47); MQ135.setB(-2.862);
  float CO2 = MQ135.readSensor();
  // Check if any reads failed and exit early (to try again).
  if (isnan(CO2)) {    
    Serial.println("CO2 PPP : Failed From Sensor!");
    return "--";
  }
  else {
    Serial.print("CO2: ");
    Serial.println(CO2);
    ThingSpeak.setField(2, CO2);
    return String(CO2);
  }
}

String readMQ135NH4() {
  // Sensor readings may also be up to 1 seconds
  // Read PPM NH4 concentration
  MQ135.setA(102.2); MQ135.setB(-2.473);
  float NH4 = MQ135.readSensor();
  // Check if any reads failed and exit early (to try again).
  if (isnan(NH4)) {    
    Serial.println("NH4 PPP : Failed From Sensor!");
    return "--";
  }
  else {
    Serial.print("NH4: ");
    Serial.println(NH4);
    ThingSpeak.setField(3, NH4);
    return String(NH4);
  }
}

String readMQ135ALC() {
  // Sensor readings may also be up to 1 seconds
  // Read PPM Alcohol concentration
  MQ135.setA(77.255); MQ135.setB(-3.18);
  float ALC = MQ135.readSensor();
  // Check if any reads failed and exit early (to try again).
  if (isnan(ALC)) {    
    Serial.println("Alcohol PPP : Failed From Sensor!");
    return "--";
  }
  else {
    Serial.print("Alcohol: ");
    Serial.println(ALC);
    ThingSpeak.setField(5, ALC);
    return String(ALC);
  }
}

String readMQ135TOL() {
  // Sensor readings may also be up to 1 seconds
  // Read PPM Toluene concentration
  MQ135.setA(44.947); MQ135.setB(-3.445);
  float TOL = MQ135.readSensor();
  // Check if any reads failed and exit early (to try again).
  if (isnan(TOL)) {    
    Serial.println("Toluene PPP : Failed From Sensor!");
    return "--";
  }
  else {
    Serial.print("Toluene: ");
    Serial.println(TOL);
    ThingSpeak.setField(4, TOL);
    return String(TOL);
  }
}

String readMQ135ACT() {
  // Sensor readings may also be up to 1 seconds
  // Read PPM Acetone concentration
  MQ135.setA(34.668); MQ135.setB(-3.369);
  float ACT = MQ135.readSensor();
  // Check if any reads failed and exit early (to try again).
  if (isnan(ACT)) {    
    Serial.println("Acetone PPP : Failed From Sensor!");
    return "--";
  }
  else {
    Serial.print("Acetone: ");
    Serial.println(ACT);
    return String(ACT);
  }
}

String readNoise() {
  float adc_ac = analogRead(noise_sensor) - 512;
  float volts = (5.0 / 1024.0) * adc_ac;
  float volts_db = 20.0 * log10(volts);
  float spl_db = volts_db + 6;
  Serial.print("Noise Level: ");
  Serial.print(spl_db);
  Serial.println(" db");
  ThingSpeak.setField(7, spl_db);
  return String(spl_db);
}

String readTemp() {
  float temp = dht.readTemperature();
  if (isnan(temp)) {    
    Serial.println("Temparature : Failed From Sensor!");
    return "--";
  }
  else {
    Serial.print("Temparature: ");
    Serial.print(temp);
    Serial.println(" °C");
    ThingSpeak.setField(8, temp);
    return String(temp);
  }
}

String readHumid() {
  float humid = dht.readHumidity();
  if (isnan(humid)) {    
    Serial.println("Humidity : Failed From Sensor!");
    return "--";
  }
  else {
    Serial.print("Humidity: ");
    Serial.print(humid);
    Serial.println("%");
    ThingSpeak.setField(6, humid);
    return String(humid);
  }
}

void setup()
{
  // Serial port for debugging purposes
  Serial.begin(115200);

  // Init Led
  pinMode(ONBOARD_LED,OUTPUT);

  // Booting
  Serial.println("Starting Device ...");
  delay(1000);

  // Led On
  digitalWrite(ONBOARD_LED, HIGH);

  // Define hostname
  WiFi.setHostname(hostname.c_str());

  // Print hostname
  Serial.print("Hostname: ");
  Serial.println(hostname);

  // Connect to Wi-Fi
  WiFi.begin(ssid, pass);
  Serial.print("Connecting to WiFi ..");
  for (int i = 0; i <= 5; i++) {
    if (WiFi.status() != WL_CONNECTED) {
      Serial.print('.');
      delay(1000);
    }
  }

  // Space Debug
  Serial.println();

  // Check Wi-Fi Connection
  if (WiFi.waitForConnectResult() == WL_CONNECTED) {
    Serial.print("Connected To WiFi AP");
  }
  else {
    Serial.println("Connection To WiFi AP Failed");
    Serial.println("Restarting Device ...");
    LED_Blink(500,5);
    ESP.restart();
  }

  // Space Debug
  Serial.println();

  // Print ESP32 SSID Mac Address
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // Print ESP32 RRSI Mac Address
  Serial.print("RRSI: ");
  Serial.println(WiFi.RSSI());

  // Print ESP32 IP Address
  Serial.print("ADIP: ");
  Serial.println(WiFi.localIP());
  
  // Print ESP32 Mac Address
  Serial.print("MACS: ");
  Serial.println(WiFi.macAddress());


  //Set math model to calculate the PPM concentration and the value of constants
  MQ135.setRegressionMethod(1); //_PPM =  a*ratio^b

  //Init Sensor
  MQ135.init();
  dht.begin();
  ThingSpeak.begin(client);  // Initialize ThingSpeak
  // In this routine the sensor will measure the resistance of the sensor supposing before was pre-heated
  // and now is on clean air (Calibration conditions), and it will setup R0 value.
  // We recomend execute this routine only on setup or on the laboratory and save on the eeprom of your arduino
  // This routine not need to execute to every restart, you can load your R0 if you know the value
  // Verbose PreHeat
  Serial.println("Calibrating ...");

  //PreHeat
  Serial.println("PreHeating ...");

  // LED Code
  digitalWrite(ONBOARD_LED,HIGH);

  //MQ CAlibration
  float calcR0 = 0;
  for(int i = 1; i<=10; i ++){
    // Update data, the arduino will be read the voltage on the analog pin
    MQ135.update();
    calcR0 += MQ135.calibrate(RatioMQ135CleanAir);
    MQ135.setR0(calcR0/10);
    // End Calibration
  }
  
  // Verobose Done
  Serial.println("Calibration Done.");

  // Wires Detection
  if(isinf(calcR0)) {
    Serial.println("Warning: Conection Issue Founded, R0 Infite : Open Circuit Detected");
    Serial.println("Restarting Device ...");
    delay(3000); LED_Blink(100,1);
    ESP.restart(); // Reboot Esp32
    }
  if(calcR0 == 0){
    Serial.println("Warning: Conection Issue Founded, R0 Zero : Analog Pin Short Circuit Ground");
    Serial.println("Restarting Device ...");
    delay(3000); LED_Blink(100,1);
    ESP.restart(); // Reboot Esp32
    }

  // Led Off
  digitalWrite(ONBOARD_LED,LOW);
  
  
}

// Loop
void loop()
{
  // if WiFi is down, try reconnecting
  if ((WiFi.status() != WL_CONNECTED)) {
    Serial.println("Disconnected From WiFi AP"); 
    Serial.println("Restarting Device ...");
    delay(5000); LED_Blink(500,5);
    ESP.restart(); // Reboot Esp32
  }  
  Serial.println("-------------------------");
  Serial.println();
  readMQ135CO().c_str();
  readMQ135CO2().c_str();
  readMQ135NH4().c_str();
  readMQ135TOL().c_str();
  readMQ135ALC().c_str();
  readMQ135ACT().c_str();
  readNoise().c_str();
  readTemp().c_str();
  readHumid().c_str();

  int x = ThingSpeak.writeFields(myChannelNumber, myWriteAPIKey);

  if(x == 200){
    Serial.println("Channel update successful.");
  }
  else{
    Serial.println("Problem updating channel. HTTP error code " + String(x));
  }
  Serial.println("Waiting...");  
  // Update data, the esp will be read the voltage on the analog pin
  MQ135.update();
  delay(1000);
}