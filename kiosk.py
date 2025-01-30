import vlc
import sys
import json
import board
import pygame
import signal
import locale
import yt_dlp
import platform
import threading
import pygame.gfxdraw
import RPi.GPIO as GPIO
import subprocess as sp
import paho.mqtt.client as paho
from time import strftime, time_ns
from const import FRANCE_TZ
from datetime import datetime
from rtetempo import APIWorker
from dataclasses import dataclass
from adafruit_htu21d import HTU21D
from collections.abc import Callable
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes 

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(9, GPIO.OUT)
GPIO.output(9, GPIO.LOW)

# Sensitive surfaces
@dataclass
class TactileZone:
    _cb: Callable[[int, str], None]
    rect: pygame.Rect
    name: str

tactile_zones = []
tactile_zones.append(TactileZone(click, pygame.Rect(270,  35,  48,  70), "boiler"))

# Set locale
locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")

# Global variables
albumart   = pygame.Surface((160, 160), pygame.SRCALPHA)
ydl_opts   = {"geturl": True, "quiet": True}
tgt_arch   = "aarch64"
bt_addr    = "41:42:50:E4:3C:4D"
first_run  = True
running    = True
boiler     = False
info       = False
animate    = False
bt_present = False
solar_pw   = 0.0
grid_pw    = 0.0
batt_pw    = 0.0
batt_max   = 5000.0
grid_max   = 6800.0
sol_max    = 2920.0
tempo_now  = 'UNKN'
tempo_tmw  = 'UNKN'
cur_batt   = '0,0%'
cur_temp   = '19.0°'
cur_hum    = '45%'
gauge_h    = 80
anim_pct   = 0
anim_dly   = 7

# Temperature sensor setup
i2c = board.I2C()  # uses board.SCL and board.SDA
sensor = HTU21D(i2c)

# pygame setup
pygame.mixer.pre_init(buffer=8192)
pygame.init()
pygame.font.init()
pygame.mixer.init()
pygame.mixer.stop()
pygame.mouse.set_visible(False)
if (platform.machine() == tgt_arch):
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode((1024, 600))
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
solar_col   = pygame.Color(255, 202,  13)

# Load assets
background    = pygame.image.load('images/background.jpg')
blue_flame    = pygame.image.load('images/blue-flame.png')
grey_flame    = pygame.image.load('images/grey-flame.png')
icon_battery  = pygame.image.load('images/icon-battery.png')
icon_grid     = pygame.image.load('images/icon-grid.png')
icon_solar    = pygame.image.load('images/icon-solar.png')
play_disabled = pygame.image.load('images/play-disabled.png')
play_enabled  = pygame.image.load('images/play-enabled.png')
pause         = pygame.image.load('images/pause.png')
next_disabled = pygame.image.load('images/next-disabled.png')
next_enabled  = pygame.image.load('images/next-enabled.png')
bt_disabled   = pygame.image.load('images/bt-disabled.png')
bt_enabled    = pygame.image.load('images/bt-enabled.png')
font_hour     = pygame.font.Font('fonts/Courgette-Regular.ttf', 200)
font_text     = pygame.font.Font('fonts/OpenSans-Medium.ttf', 24)
font_date     = pygame.font.Font('fonts/OpenSans-Medium.ttf', 36)
font_batt     = pygame.font.Font('fonts/OpenSans-Medium.ttf', 50)
font_temp     = pygame.font.Font('fonts/OpenSans-Medium.ttf', 65)
font_hum      = pygame.font.Font('fonts/OpenSans-Medium.ttf', 65)

# Timer events
TEMPO_TICK = pygame.event.custom_type()
TEMP_TICK  = pygame.event.custom_type()
MQTT_TICK  = pygame.event.custom_type()
BOILER_OFF = pygame.event.custom_type()
INFO_OFF   = pygame.event.custom_type()
ANIMATE    = pygame.event.custom_type()
pygame.time.set_timer(TEMPO_TICK, 120000)
pygame.time.set_timer(MQTT_TICK,   30000)
pygame.time.set_timer(TEMP_TICK,    3000)

# RTE Tempo setup
api_worker = APIWorker(
    client_id="ece3f4f6-b4c0-490c-a79a-23d6795603ed",
    client_secret="1da24e80-1b13-416b-baf9-91a0c652c1a6",
    adjusted_days=False
)
api_worker.start()

# MQTT client setup
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

properties=Properties(PacketTypes.PUBLISH)
properties.MessageExpiryInterval=5 # in seconds
client = paho.Client(paho.CallbackAPIVersion.VERSION2, "Kiosk")
#client.on_log = on_log
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
    min_h = 5
    height = int(((gauge_h - min_h) * (100 - anim_pct) / 100) + min_h)
    count = int(height * pct / 100)
    n = 0
    
    pygame.draw.rect(screen, fground_col, (765, base - height - 2, 23, height + 6), 0, 8)
    if rev:
        for y in range(base - height, base - height + count):
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
    global cur_temp
    global cur_hum
    global grid_pw
    global batt_pw
    global solar_pw
    global tactile_zones
    global boiler
    global info
    global anim_pct
    global first_run

    cur_time = strftime('%H:%M')
    cur_date = strftime('%A ') + strftime('%d').lstrip('0') + strftime(' %B %Y')

#    for zone in tactile_zones:
#        pygame.draw.rect(screen, fground_col, zone.rect, 1, 10)

    screen.blit(background, (0, 0))

    tempoDraw(tempo_now, (863, 63), 17)
    tempoDraw(tempo_tmw, (900, 67), 13)
    r = pygame.Rect(699 - anim_pct, 112, 269 + anim_pct, 432)
    pygame.draw.rect(screen, fground_col, r, 2, 33)
    if first_run:
      tactile_zones.append(TactileZone(click, r, "info"))
    if anim_pct != 100:
        gaugeDraw(216, int(100.0 * solar_pw / sol_max), solar_col)
        if grid_pw > 0.0:
            gaugeDraw(327, int( 100.0 * grid_pw / grid_max), grid_fw_col)
        else:
            gaugeDraw(327, int(-100.0 * grid_pw / grid_max), grid_bw_col, True)
        if batt_pw > 0.0:
            gaugeDraw(438, int( 100.0 * batt_pw / batt_max), bat_chg_col)
        else:
            gaugeDraw(438, int(-100.0 * batt_pw / batt_max), bat_dch_col, True)
    else:
        pass
        y = 180
        for watt in [ solar_pw, grid_pw, batt_pw ]:
            text_srf = font_batt.render("%dW" % watt, True, fground_col, None)
            text_crd = text_srf.get_rect()
            text_crd.midright = (805, y)
            screen.blit(text_srf, text_crd)
            y += 111

    date_srf = font_date.render(cur_date, True, fground_col, None)
    date_crd = date_srf.get_rect()
    date_crd.center = (295, 150)

    hour_srf = font_hour.render(cur_time, True, fground_col, None)
    hour_crd = hour_srf.get_rect()
    hour_crd.center = (300, 300)

    temp_srf = font_temp.render(cur_temp, True, fground_col, None)
    temp_crd = temp_srf.get_rect()
    temp_crd.center = (180,  80)

    hum_srf  = font_hum.render (cur_hum , True, fground_col, None)
    hum_crd  = hum_srf.get_rect()
    hum_crd.center =  (390,  80)

    batt_srf = font_batt.render(cur_batt, True, fground_col, None)
    batt_crd = batt_srf.get_rect()
    batt_crd.center = (830,  485)

    text_srf = font_text.render('Tempo', True, fground_col, None)
    text_crd = text_srf.get_rect()
    text_crd.center = (788,   65)

    screen.blit(hour_srf, hour_crd)
    screen.blit(date_srf, date_crd)
    screen.blit(temp_srf, temp_crd)
    screen.blit(hum_srf,  hum_crd)
    screen.blit(batt_srf, batt_crd)
    screen.blit(text_srf, text_crd)
    if boiler:
        screen.blit(blue_flame, (275, 50))
    else:
        screen.blit(grey_flame, (275, 50))
    screen.blit(icon_solar,     (830, 138))
    screen.blit(icon_grid,      (830, 251))
    screen.blit(icon_battery,   (830, 361))
    if bt_present:
        img = play_enabled
    else:
        img = play_disabled
    r = screen.blit(img , (225, 453))
    if first_run:
        tactile_zones.append(TactileZone(click, r, "play"))
    if bt_present:
        img = next_enabled
    else:
        img = next_disabled
    r = screen.blit(img,  (322, 453))
    if first_run:
        tactile_zones.append(TactileZone(click, r, "next"))
    if bt_present:
        img = bt_enabled
    else:
        img = bt_disabled
    r = screen.blit(img, (427, 453))
    if first_run:
        tactile_zones.append(TactileZone(click, r, "bt"))
    screen.blit(albumart, (20, 400))

    pygame.display.flip()
    first_run = False

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

def signal_handler(sig, frame):
    global running
    running = False

def click(duration_ms, name):
    global boiler
    global info

    if duration_ms > 1000: # very long press
        print("Very long click on", name)
    elif duration_ms > 150: # long press
        print("Long click on", name)
        match name:
            case "boiler":
                if boiler:
                    GPIO.output(9, GPIO.LOW)
                else:
                    GPIO.output(9, GPIO.HIGH)
                    pygame.time.set_timer(BOILER_OFF, 20*60000, 1)
    else: # short press
        print("Short click on", name)
        match name:
            case "info":
                if not info:
                    info = True
                    pygame.time.set_timer(INFO_OFF, 30000,  1)
                    pygame.time.set_timer(ANIMATE, anim_dly, 100)

def getImage(url):
    global albumart

    r = requests.get(url)
    img = io.BytesIO(r.content)
    s = pygame.image.load(img, namehint="") # -> Surface
    albumart = s

#### MAIN ####
signal.signal(signal.SIGINT, signal_handler)
# Main loop
while running:
    # limit to 60fps to prevent CPU overload
    clock.tick(60)
    boiler = GPIO.input(9)

    # poll for events
    for event in pygame.event.get():
        # pygame.QUIT event means the user clicked X to close your window
        if event.type == pygame.QUIT:
            running = False
        elif event.type in [pygame.MOUSEMOTION, pygame.VIDEOEXPOSE, pygame.ACTIVEEVENT]:
            pass
        elif event.type in [pygame.FINGERDOWN, pygame.FINGERUP]:
            pass
        elif event.type in [pygame.AUDIODEVICEREMOVED, pygame.AUDIODEVICEADDED]:
            pass
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_press = time_ns()
        elif event.type == pygame.MOUSEBUTTONUP:
            mouse_press = time_ns() - mouse_press
            for zone in tactile_zones:
                if zone.rect.collidepoint(pygame.mouse.get_pos()):
                    zone._cb(int(mouse_press/1000000), zone.name)
        elif event.type in [pygame.WINDOWLEAVE, pygame.WINDOWENTER, pygame.WINDOWCLOSE, pygame.WINDOWEXPOSED, pygame.WINDOWSIZECHANGED, pygame.WINDOWSHOWN, pygame.WINDOWHIDDEN, pygame.WINDOWFOCUSGAINED]:
            pass
        elif event.type == MQTT_TICK:
            client.publish('R/d83add91edfc/keepalive','{ "keepalive-options" : ["suppress-republish"] }', 2, properties=properties)
        elif event.type == TEMPO_TICK:
            tempoUpdate()
        elif event.type == TEMP_TICK:
            bt_present = bt_addr in sp.getoutput("hcitool con").split()
            buf = "%0.1f°" % sensor.temperature
            cur_temp = buf.replace(".", ",")
            cur_hum  = "%d%%" % int(sensor.relative_humidity)
        elif event.type == BOILER_OFF:
            GPIO.output(9, GPIO.LOW)
        elif event.type == INFO_OFF:
            info = False
            pygame.time.set_timer(ANIMATE, anim_dly, 100)
        elif event.type == ANIMATE:
            if info:
                anim_pct += 1
            else:
                anim_pct -= 1
        else:
            print("Unknown event %d", event.type)

    buildMainUI()

api_worker.signalstop("Kiosk shutdown")
client.loop_stop()
client.disconnect()
pygame.quit()
