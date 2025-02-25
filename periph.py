from time import sleep
from platform import machine
from board import I2C
from adafruit_htu21d import HTU21D

relay  = None
rpi    = machine() in ("armv6l", "armv7l", "aarch64")

# Temperature sensor setup
if rpi:
    sensor = HTU21D(I2C())
else:
    sensor = None

def boiler_relay(cmd = "Query"):
    global relay
    global rpi

    if cmd == 'Init':
        print("Relay Init on", machine())
        if rpi:
            from gpiozero import LED
            relay = LED("GPIO9")
            relay.off()
        else:
            print(machine(), "is not an RPi")
            return(False)
    if relay == None:
        return False
    if cmd == 'OFF':
        print("Relay OFF")
        relay.off()
    if cmd == 'ON':
        print("Relay ON")
        relay.on()
    return relay.value == 1

if __name__ == "__main__":
    boiler_relay('Init')
    print(boiler_relay())
    sleep(1)
    boiler_relay('ON')
    print(boiler_relay())
    sleep(5)
    boiler_relay('OFF')
    print(boiler_relay())
