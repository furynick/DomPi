import json
import pygame
import pygame.gfxdraw
import paho.mqtt.client as paho
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes 
from time import sleep, strftime, time_ns
from datetime import datetime
from rtetempo import APIWorker
from const import FRANCE_TZ

# Global variables
running = True
cur_time = '66:66'
cur_date = ''
cur_temp = '18,3°'
cur_batt = '100.0%'
tempo_now = 'UNKN'
tempo_tmw = 'UNKN'

# pygame setup
pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((1024, 600))
clock  = pygame.time.Clock()

# Colors setup
bground_col = pygame.Color(  0,   0,   0)
tempo_r_col = pygame.Color(220,   0,   0)
tempo_w_col = pygame.Color(220, 220, 220)
tempo_b_col = pygame.Color(  0,   0, 220)
tempo_u_col = pygame.Color( 60,  60,  60)
seconds_col = pygame.Color( 11, 156, 215)
wtmask_col  = pygame.Color(127, 127, 127, 127)

# Timer events
TEMPO_TICK = pygame.event.custom_type()
MQTT_TICK  = pygame.event.custom_type()
pygame.time.set_timer(TEMPO_TICK, 120000)
pygame.time.set_timer(MQTT_TICK,   50000)

# RTE Tempo setup
api_worker = APIWorker(
    client_id="ece3f4f6-b4c0-490c-a79a-23d6795603ed",
    client_secret="1da24e80-1b13-416b-baf9-91a0c652c1a6",
    adjusted_days=False
)
api_worker.start()

# MQTT client setup
def on_connect(client, userdata, flags, reason_code, properties=None):
    client.subscribe(topic="N/d83add91edfc/battery/292/Soc")
    client.subscribe(topic="N/d83add91edfc/battery/292/Dc/0/Power")
    client.subscribe(topic="N/d83add91edfc/grid/30/Ac/Power")
    client.subscribe(topic="N/d83add91edfc/pvinverter/20/Ac/Power")
    client.publish('R/d83add91edfc/keepalive','{ "keepalive-options" : ["suppress-republish"] }', 2, properties=properties)

def on_connect_fail(client, userdata):
    print('CONNFAIL received with data %s.' % (userdata))

def on_message(client, userdata, message, properties=None):
    global cur_batt

    payload = json.loads(message.payload)
    match message.topic:
        case "N/d83add91edfc/battery/292/Soc":
            print(f"{datetime.now()} Received SoC value {payload['value']}")
            cur_batt = "%0.1f%%" % float(payload['value'])
        case "N/d83add91edfc/battery/292/Dc/0/Power":
            print(f"{datetime.now()} Received Battery value {payload['value']}")
        case "N/d83add91edfc/grid/30/Ac/Power":
            print(f"{datetime.now()} Received Grid value {payload['value']}")
        case "N/d83add91edfc/pvinverter/20/Ac/Power":
            print(f"{datetime.now()} Received Inverter value {payload['value']}")

def on_subscribe(client, userdata, mid, qos, properties=None):
    print(f"{datetime.now()} Subscribed with QoS {qos}")

properties=Properties(PacketTypes.PUBLISH)
properties.MessageExpiryInterval=5 # in seconds
client = paho.Client(paho.CallbackAPIVersion.VERSION2, "Kiosk")
client.on_connect = on_connect
client.on_connect_fail = on_connect_fail
client.on_message = on_message
client.on_subscribe = on_subscribe
try:
    client.connect('192.168.0.141', 1883)
except ConnectionRefusedError:
    print("Unable to connect")
except:
    print("Unknown MQTT connect error")
else:
    client.loop_start()

# Load assets
background = pygame.image.load('background.png')
blue_flame = pygame.transform.scale(pygame.image.load('blue-flame.png'), (23,50))
grey_flame = pygame.transform.scale(pygame.image.load('grey-flame.png'), (23,50))
font_date  = pygame.font.SysFont('ubuntu', 32)
font_hour  = pygame.font.Font('Courgette-Regular.ttf', 200)
font_temp  = pygame.font.SysFont('ubuntu', 65)
font_batt  = pygame.font.SysFont('ubuntu', 50)

def tempoDraw(state, c, r):
    col = tempo_u_col
    match state:
        case 'BLUE':
            col = tempo_b_col
        case 'WHITE':
            col = tempo_w_col
        case 'RED':
            col = tempo_r_col
            
    pygame.gfxdraw.aacircle(screen, c[0], c[1], r, col)
    pygame.gfxdraw.filled_circle(screen, c[0], c[1], r, col)

# Redraw full screen function
def redraw():
    global tempo_now
    global tempo_tmw
    global cur_batt

    screen.blit(background, (0, 0))
    date_srf = font_date.render(cur_date, True, "white", None)
    temp_srf = font_temp.render(cur_temp, True, "white", None)
    hour_srf = font_hour.render(cur_time, True, "white", None)
    batt_srf = font_batt.render(cur_batt, True, "white", None)
    date_crd = date_srf.get_rect()
    date_crd.center = (295, 150)
    hour_crd = hour_srf.get_rect()
    hour_crd.center = (300, 300)
    temp_crd = temp_srf.get_rect()
    temp_crd.center = (180,  80)
    batt_crd = batt_srf.get_rect()
    batt_crd.center = (830,  485)
    
    tempoDraw(tempo_now, (863, 68), 17)
    tempoDraw(tempo_tmw, (900, 72), 13)
    
    screen.blit(hour_srf,   hour_crd)
    screen.blit(date_srf,   date_crd)
    screen.blit(blue_flame, (260, 60))
    screen.blit(temp_srf,   temp_crd)
    screen.blit(batt_srf,   batt_crd)
    pygame.display.flip()

def tempoUpdate():
    global tempo_now
    global tempo_tmw

    tempo_now = 'UNKN'
    tempo_tmw = 'UNKN'
    localized_now = datetime.now(FRANCE_TZ)
    t = api_worker.get_adjusted_days()
    for tempo_day in t:
        if tempo_day.Start <= localized_now < tempo_day.End:
            tempo_now=tempo_day.Value
        if localized_now < tempo_day.Start:
            tempo_tmw=tempo_day.Value

# Main loop
track_tempo = True
while running:
    # limit to 60fps to prevent CPU overload
    clock.tick(60)

    # poll for events
    for event in pygame.event.get():
        # pygame.QUIT event means the user clicked X to close your window
        if event.type == pygame.QUIT:
            running = False
        elif event.type ==  MQTT_TICK:
            client.publish('R/d83add91edfc/keepalive','{ "keepalive-options" : ["suppress-republish"] }', 2, properties=properties)
        elif event.type ==  TEMPO_TICK:
            tempoUpdate()
        else:
            print("Unknown %d", event.type)

    cur_time = strftime('%H:%M')
    cur_date = strftime('%A %-d %B %Y')
    redraw()

api_worker.signalstop("Kiosk shutdown")
client.disconnect()
pygame.quit()
