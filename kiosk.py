import locale
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

# Set locale
locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")

# Global variables
bt_addr   = "60:6D:C7:70:A6:34"
running   = True
boiler    = False
solar_pw  = 0.0
grid_pw   = 0.0
batt_pw   = 0.0
cur_temp  = '18,3°'
cur_batt  = '0.0%'
tempo_now = 'UNKN'
tempo_tmw = 'UNKN'
batt_max  = 5000.0
grid_max  = 6800.0
sol_max   = 2920.0

# pygame setup
pygame.init()
pygame.font.init()
pygame.mouse.set_visible(False)
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock  = pygame.time.Clock()

# Colors setup
bground_col = pygame.Color(  0,   0,   0)
fground_col = pygame.Color(240, 240, 240)
tempo_r_col = pygame.Color(220,   0,   0)
tempo_w_col = pygame.Color(220, 220, 220)
tempo_b_col = pygame.Color(  0,   0, 220)
tempo_u_col = pygame.Color( 60,  60,  60)
seconds_col = pygame.Color( 11, 156, 215)
bat_dch_col = pygame.Color(225, 142, 233)
bat_chg_col = pygame.Color( 71, 144, 208)
grid_fw_col = pygame.Color(233, 122, 131)
grid_bw_col = pygame.Color(212, 222,  95)
solar_col   = pygame.Color(244, 232,  13)

# Load assets
background  = pygame.image.load('background.png')
blue_flame  = pygame.image.load('blue-flame.png')
grey_flame  = pygame.image.load('grey-flame.png')
font_hour   = pygame.font.Font('Courgette-Regular.ttf', 200)
font_date   = pygame.font.SysFont('ubuntu', 36)
font_batt   = pygame.font.SysFont('ubuntu', 50)
font_temp   = pygame.font.SysFont('ubuntu', 65)

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
    global solar_pw
    global grid_pw
    global batt_pw

    payload = json.loads(message.payload)
    match message.topic:
        case "N/d83add91edfc/battery/292/Soc":
            str = "%0.1f%%" % float(payload['value'])
            cur_batt = str.replace(".", ",")
        case "N/d83add91edfc/battery/292/Dc/0/Power":
            batt_pw = float(payload['value'])
        case "N/d83add91edfc/grid/30/Ac/Power":
            grid_pw = float(payload['value'])
        case "N/d83add91edfc/pvinverter/20/Ac/Power":
            solar_pw = float(payload['value'])

def on_subscribe(client, userdata, mid, qos, properties=None):
    print(f"{datetime.now()} Subscribed with QoS {qos}")

properties=Properties(PacketTypes.PUBLISH)
properties.MessageExpiryInterval=5 # in seconds
client = paho.Client("Kiosk")
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

def gaugeDrawLine(x, y, n, c):
    l=18
    for i in range(5, 1, -1):
        if n < i:
            l -= 2
            x += 1
    pygame.draw.line(screen, c, (x, y), (x + l, y))

def gaugeDraw(base, pct, col, rev = False):
    count = int(60 * pct / 100)
    n = 0
    
    if rev:
        for y in range(base - 60, base - 60 + count):
            n += 1
            gaugeDrawLine(767, y, n, col)
    else:
        for y in range(base, base - count, -1):
            n += 1
            gaugeDrawLine(767, y, n, col)

# Redraw full screen function
def buildMainUI():
    global tempo_now
    global tempo_tmw
    global cur_batt
    global grid_pw
    global batt_pw
    global solar_pw

    cur_time = strftime('%H:%M')
    cur_date = strftime('%A %-d %B %Y')

    screen.blit(background, (0, 0))
    date_srf = font_date.render(cur_date, True, fground_col, None)
    temp_srf = font_temp.render(cur_temp, True, fground_col, None)
    hour_srf = font_hour.render(cur_time, True, fground_col, None)
    batt_srf = font_batt.render(cur_batt, True, fground_col, None)
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
    if batt_pw > 0.0:
        gaugeDraw(390, int( 100.0 * batt_pw / batt_max), bat_chg_col)
    else:
        gaugeDraw(390, int(-100.0 * batt_pw / batt_max), bat_dch_col, True)
    if grid_pw > 0.0:
        gaugeDraw(299, int( 100.0 * grid_pw / grid_max), grid_fw_col)
    else:
        gaugeDraw(299, int(-100.0 * grid_pw / grid_max), grid_bw_col, True)
    gaugeDraw(208, int(100.0 * solar_pw / sol_max), solar_col)

    screen.blit(hour_srf,   hour_crd)
    screen.blit(date_srf,   date_crd)
    screen.blit(temp_srf,   temp_crd)
    screen.blit(batt_srf,   batt_crd)
    if boiler:
        screen.blit(blue_flame, (275, 45))
    else:
        screen.blit(grey_flame, (275, 45))
    pygame.display.flip()

def tempoUpdate():
    global tempo_now
    global tempo_tmw

    tempo_now = 'UNKN'
    tempo_tmw = 'UNKN'
    localized_now = datetime.now(FRANCE_TZ)
    for tempo_day in api_worker.get_adjusted_days():
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
        elif event.type == pygame.MOUSEMOTION:
            pass
        elif event.type == pygame.WINDOWLEAVE:
            pass
        elif event.type == pygame.WINDOWENTER:
            pass
        elif event.type == pygame.WINDOWCLOSE:
            pass
        elif event.type == MQTT_TICK:
            client.publish('R/d83add91edfc/keepalive','{ "keepalive-options" : ["suppress-republish"] }', 2, properties=properties)
        elif event.type == TEMPO_TICK:
            tempoUpdate()
        else:
            print("Unknown %d", event.type)

    buildMainUI()

api_worker.signalstop("Kiosk shutdown")
client.disconnect()
pygame.quit()
