import json
from datetime import datetime
import paho.mqtt.client as paho
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes 

client   = paho.Client(paho.CallbackAPIVersion.VERSION2, "Kiosk")
cur_batt = '0,0%'
solar_pw = 0.0
grid_pw  = 0.0
batt_pw  = 0.0

def on_log(client, userdata, level, buf):
    print("log: ",buf)

def on_connect(client, userdata, flags, reason_code, properties=None):
    client.subscribe(topic="N/d83add91edfc/battery/291/Soc")
    client.subscribe(topic="N/d83add91edfc/grid/30/Ac/Power")
    client.subscribe(topic="N/d83add91edfc/battery/291/Dc/0/Power")
    client.subscribe(topic="N/d83add91edfc/pvinverter/20/Ac/Power")
    client.publish('R/d83add91edfc/keepalive','{ "keepalive-options" : ["suppress-republish"] }', 2, properties=properties)

def on_connect_fail(client, userdata):
    print('CONNFAIL received with data %s.' % (userdata))

def on_message(client, userdata, message, properties=None):
    global cur_batt
    global solar_pw
    global grid_pw
    global batt_pw

    try:
        payload = json.loads(message.payload)
        value = float(payload['value'])
    except json.decoder.JSONDecodeError as e:
        print("Error decoding JSON", message)
        value = 0.0
    except ValueError as e:
        print("Error decoding", message)
        value = 0.0
    except TypeError as e:
        print("Invalid type", message)
        value = 0.0
    match message.topic:
        case "N/d83add91edfc/battery/291/Soc":
            buf = "%0.1f%%" % value
            cur_batt = buf.replace(".", ",")
        case "N/d83add91edfc/battery/291/Dc/0/Power":
            batt_pw = value
        case "N/d83add91edfc/grid/30/Ac/Power":
            grid_pw = value
        case "N/d83add91edfc/pvinverter/20/Ac/Power":
            solar_pw = value

def on_subscribe(client, userdata, mid, qos, properties=None):
    print(f"{datetime.now()} Subscribed with QoS {qos}")

def setup(addr, port=1883):
    global client

    #client.on_log = on_log
    client.on_connect = on_connect
    client.on_connect_fail = on_connect_fail
    client.on_message = on_message
    client.on_subscribe = on_subscribe
    try:
        client.connect(addr, port)
    except ConnectionRefusedError:
        print("Unable to connect")
    except:
        print("Unknown MQTT connect error")
    else:
        client.loop_start()

def keepalive():
    global client

    properties=Properties(PacketTypes.PUBLISH)
    properties.MessageExpiryInterval=5 # in seconds
    client.publish('R/d83add91edfc/keepalive','{ "keepalive-options" : ["suppress-republish"] }', 2, properties=properties)

def shutdown():
    global client

    client.loop_stop()
    client.disconnect()
