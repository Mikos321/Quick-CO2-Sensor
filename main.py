import network
import time
from machine import Pin
from umqtt.simple import MQTTClient
from machine import I2C, Pin
from scd30 import SCD30
import json
import secrets
import gc
i2c = machine.I2C(0,scl=machine.Pin(17), sda=machine.Pin(16))
scd30 = SCD30(i2c, 0x61)
led = machine.Pin("LED",machine.Pin.OUT)
print('Running')
#Manual calibration:
scd30.set_forced_recalibration(400)

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