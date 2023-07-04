# Pico CO2 Sensor
**By Love Suneson (ls224zc)**
2023-07-04

## Objective

Spending time by my computer, sitting at my desk has it's drawbacks, one of which is that unless my window is open there seems to be somewhat low airflow around the desk. I wondered if Carbondioxide (CO2) would build up by my desk and if so, it would be handy to have a notification telling me to open my window. Utilizing my already setup Home assistant server and MQTT broker I build a quick wifi connected CO2 meter using a PICO-W and a Adafruit SCD-30 module. Assuming you have a Home assistant instance running, I'd say this project would take about an hour to set up.


### Material

 |Product|Where to buy| Description |Price|
|---|---|---|---|
|Raspberry pi Pico WH|Electrokit|Cheap but powerful microcontroller based on the RP2040 microprocessor and an infineon43439 wifi chip with presoldered pinheaders|109 kr|
|Adafruit SDC-30|Electrokit|A CO2, humidity and temperature sensor that can measure actual Carbon dioxide concentrations in the air|995 kr|
|Breadboard|Electrokit|A board with interconnects that makes it easier to connect socketed devices together |49kr (400pins)|
|Jumper wires|Electrokit|---|49kr / 40 pieces|
|USB type micro B Cable|Electrokit|---|16kr / 15cm


I use the adafruit SCD30 module which is based on the Sensirion SCD30 Sensor. It measures actual CO2 concetration compared to other sensors which only estimates from VOC (volotile organic compounds) - measurements. The SCD30 also measures temperature and humidity. It can either be manually calibrated or use a autocalibration feature. I use the manual calibration as it requires to be run continiously and be exposed to fresh air regulary. I have not been able to keep my code stable enough and since i don't have a battery it makes it somewhat anoying to pull over to my window from time to time. I simply keep the sensor by the window when i start it up and during startup the sensor will set it's calibration to 400PPM (I assume that the outside air has a CO2 concentration of 400PPM)

### Computer setup

I used Thonny mainly to load firmware onto the pico. But even though Thonny has worse IDE features compared to VScode, I still wrote all of the code for the pico in the Thonny editor. Aswell as using the build in package manager to load libraries on to the pico automatically. 

### Putting everything together
[[Pictures/picow-pinout (2).PNG]]
Connecting the SCD30 module to the Pico W is very easy. Simply place the pico and SCD30 on the breadboard and connect the one of the GND pins on the pico to the GND pin on the SCD30. Then connect either VSYS,VBUS or 3v3(OUT) to the VIN pin on the SCD30. If you do like I did in the Fritzing circuit you bypass the internal voltage regulator so you can only plug in from 3v3(OUT) on the pico. Lastly connect I2C0 SCL on the pico to the SCL pin on the SCD30 and likewise fro the I2C0 SDA to the SDA pin on SCD30.

[[Pictures/Circuit.png]]
### Platform

I send the data collected from the SCD-30 to my Home Assistant server which I had already set up. Home assistant is an open source smart home platform where you can connect different types of smart home platforms to make them work together. In my case it is running locally on a raspberry pi4 under docker, aswell as a MQTT broker. I won't go into how you set those up as there are way better guides on the [Home assistant wiki](https://www.home-assistant.io/docs/) for that.
Id recommend that you follow Home assistants advice and run HASSOS on a raspberry pi and not use the docker version like I am.

### The code

The full code can be found in the repo.

I mainly followed the official Raspberry pi Pico W [guide](#https://projects.raspberrypi.org/en/projects/get-started-pico-w ) on how to setup networking  utilizing the Pico-zero library you get the machine and network modules.
```
def connect():
    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(secrets.ssid, secrets.password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        time.sleep(1)
    print(wlan.ifconfig())

try:
    connect()
except KeyboardInterrupt:
    machine.reset()
```

Above is the code needed to connect your pico w to your home network. I put my network credentials and other "secret" information into another python file that i call secrets.
In secrets.py:
```
ssid ='insert wifi name'
password 'insert wifi password'
```

To connect to the MQTT broker I use the [umqtt.simple library](https://pypi.org/project/micropython-umqtt.simple/) 
```
client_id = 'SCD30'
topic_pub = b'SCD30'

def mqtt_connect():
    client = MQTTClient(client_id, secrets.mqtt_ip, keepalive=3600)
    client.connect()
    print('Connected to MQTT Broker')
    return client
def reconnect():
    print('Failed to connect to the MQTT Broker. Reconnecting...')
    time.sleep(5)
    machine.reset()
try:
    client = mqtt_connect()
except OSError as e:
    reconnect()
```
If the reconnect fails it will restart the pico and try again. I print some text as a sanity check.

And finally everytime the SCD30 is ready to send data I reformat the data into json using the [json library](https://docs.micropython.org/en/latest/library/json.html) to make it easier to use in Home Assistant and publish it to the MQTT broker. If the pico is faster it waits for 200ms.
```
while True:
    led.on()
    while scd30.get_status_ready() != 1:
        time.sleep_ms(200)
    data=(scd30.read_measurement())
    topic_msg = json.dumps(data)  
    client.publish(topic_pub, topic_msg)
    print('data sent')
    gc.collect() # manual garbage collection sort of fixes some stability issues :)
    time.sleep(3)
    led.off()
    time.sleep(3)
```
As a sanity check i blink the pico W led when data is being transmitted.
I also use manual garbage collection to prevent the picos memory filling up. (this can be improved.)

#### Home Assistant:

HASS configuration.yaml:
```
mqtt:
  sensor:
    - name: "CO2"
      state_topic: "SCD30"
      suggested_display_precision: 1
      unit_of_measurement: "ppm"
      value_template: "{{ value_json[0] }}"
    - name: "Temperature"
      state_topic: "SCD30"
      suggested_display_precision: 1
      unit_of_measurement: "°C"
      value_template: "{{ value_json[1] }}"
    - name: "Humidity"
      state_topic: "SCD30"
      unit_of_measurement: "%"
      value_template: "{{ value_json[2] }}"
```

In home assistant adding sensors from an MQTT broker has to be done manually in the configuration.yaml file.
Home assistant is simply listening to the topics being sent on the MQTT broker.

### Transmitting the data / connectivity

The Pico W is connected to my Homeassistant server though Wifi, since I was going to be using the sensor at home. MQTT was used to make it easier to interface with home assistant and the data is being transmitted about every 30 seconds, I run the pico of a phone charger so I haven't really cared about power efficiency.
### Presenting the data
[[Pictures/Dashboard_CO2.png]]
All data is stored on my Home Assistant server, untill I shut it down (since I have sort of messed up my permanent storage.) The picture above shows how the data is being displayed in my Home Assistant dashboard using the Gauge card. Data graphs can be shown in the history page for the sensor
[[Pictures/HASSgraph.png]]
The straight allmost squarewave in the beginning is where the pico crashed. after about 20:12 is where good measurements are started. and you can see that the PPM value is gradually increasing since i closed the window at about 20:51.

### Finalizing the design
[[Pictures/Final sensor.jpg]]
My sensor ended up staying on the breadboard, I could go to my local makerspace and make a circuitboard to mount it all on and 3D print a case, that might be something for the future when I need the breadboard for other things. The measurements are interesting. I find that the CO2 values are lower than i expected, but also very interesting how fast it actually increases. Sadly the graph pictures I have in this tutorial does not show that long time scales. I ran the sensor at the end of may for quite some time however some instability issues that I think i solved using manual garbage collection made it too anoying to keep it running. And sadly it seems that my home assistant server restarted since then.

