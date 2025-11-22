import mqtt
import pygame
import signal
import locale
import threading
import webserver
import global_vars
import pygame.gfxdraw
from time import strftime, time_ns
from const import FRANCE_TZ
from periph import boiler_relay, rpi, sensor
from datetime import datetime
from sdnotify import SystemdNotifier
from rtetempo import APIWorker
from dataclasses import dataclass
from collections.abc import Callable

# Sensitive surfaces
@dataclass
class TactileZone:
    _cb: Callable[[int, str], None]
    rect: pygame.Rect
    name: str
    page: str

# Set locale
try:
    locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")
except:
    pass

# Global variables
info             = False
forced           = False
first_run        = True
display_cur      = True
batt_max         = 5000.0
grid_max         = 6800.0
sol_max          = 2920.0
tempo_now        = 'UNKN'
tempo_tmw        = 'UNKN'
cur_temp         = '19,0°'
cur_hum          = '45%'
ui_page          = 'main'
target_temp      = 19.0
anim_pct         = 0
anim_dly         = 5
gauge_h          = 80

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

# Redraw main screen
def buildMainUI():
    global cur_hum
    global anim_pct
    global cur_temp
    global first_run
    global tempo_now
    global tempo_tmw
    global font_hour
    global target_temp
    global display_cur

    cur_time = strftime('%H:%M')
    cur_date = strftime('%A ') + strftime('%d').lstrip('0') + strftime(' %B %Y')

    screen.blit(background, (0, 0))

    tempoDraw(tempo_now, (863, 63), 17)
    tempoDraw(tempo_tmw, (900, 67), 13)
    r = pygame.Rect(699 - anim_pct, 112, 269 + anim_pct, 432)
    if first_run:
        tactile_zones.append(TactileZone(click_main, r, "info", "main"))
    pygame.draw.rect(screen, fground_col, r, 2, 33)
    if anim_pct != 100:
        gaugeDraw(216, int(100.0 * mqtt.solar_pw / sol_max), solar_col)
        if mqtt.grid_pw > 0.0:
            gaugeDraw(327, int( 100.0 * mqtt.grid_pw / grid_max), grid_fw_col)
        else:
            gaugeDraw(327, int(-100.0 * mqtt.grid_pw / grid_max), grid_bw_col, True)
        if mqtt.batt_pw > 0.0:
            gaugeDraw(438, int( 100.0 * mqtt.batt_pw / batt_max), bat_chg_col)
        else:
            gaugeDraw(438, int(-100.0 * mqtt.batt_pw / batt_max), bat_dch_col, True)
    else:
        pass
        y = 180
        for watt in [ mqtt.solar_pw, mqtt.grid_pw, mqtt.batt_pw ]:
            text_srf = font_batt.render("%dW" % watt, True, fground_col, None)
            text_crd = text_srf.get_rect()
            text_crd.midright = (805, y)
            screen.blit(text_srf, text_crd)
            y += 111

    date_srf = font_date.render(cur_date, True, fground_col, None)
    date_crd = date_srf.get_rect()
    date_crd.center = (330, 190)

    hour_pos = 330
    if (anim_pct > 0):
        font_hour = pygame.font.Font('fonts/Courgette-Regular.ttf', 240 - int(40 * anim_pct / 100))
        hour_pos -= int(30 * anim_pct / 100)
    hour_srf = font_hour.render(cur_time, True, fground_col, None)
    hour_crd = hour_srf.get_rect()
    hour_crd.center = (hour_pos, 380)

    if display_cur:
        temp_srf = font_temp.render(cur_temp, True, fground_col, None)
    else:
        buf = "%0.1f°" % target_temp
        temp_srf = font_temp.render(buf.replace(".", ","), True, target_col, None)
    temp_crd = temp_srf.get_rect()
    temp_crd.center = (255, 100)

    hum_srf  = font_hum.render (cur_hum , True, fground_col, None)
    hum_crd  = hum_srf.get_rect()
    hum_crd.center =  (465, 100)

    batt_srf = font_batt.render(mqtt.cur_batt, True, fground_col, None)
    batt_crd = batt_srf.get_rect()
    batt_crd.center = (830,  485)

    text_srf = font_text.render('Tempo', True, fground_col, None)
    text_crd = text_srf.get_rect()
    text_crd.center = (788,   65)

    screen.blit(hour_srf, hour_crd)
    screen.blit(date_srf, date_crd)
    r = screen.blit(temp_srf, temp_crd)
    tactile_zones.append(TactileZone(click_main, r, "temp", "main"))
    screen.blit(hum_srf,  hum_crd)
    screen.blit(batt_srf, batt_crd)
    screen.blit(text_srf, text_crd)
    if boiler_relay():
        r = screen.blit(blue_flame, (350, 70))
    else:
        r = screen.blit(grey_flame, (350, 70))
    if first_run:
        tactile_zones.append(TactileZone(click_main, r, "boiler", "main"))
    screen.blit(icon_solar,     (830, 138))
    screen.blit(icon_grid,      (830, 251))
    screen.blit(icon_battery,   (830, 361))
    first_run = False

def buildSchedUI():
    global ui_page

    ui_page = "main"

def build_ui():
    if ui_page == "main":
        buildMainUI()
    elif ui_page == "schedule":
        buildSchedUI()
    pygame.display.flip()
    # limit to 50fps to prevent CPU overload
    clock.tick(50)

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
    print(" Interrupt catched")
    stop_event.set()

def click_main(duration_ms, name):
    global info
    global forced
    global display_cur

    if duration_ms > 1000: # very long press
        print("Very long click on", name)
    elif duration_ms > 150: # long press
        print("Long click on", name)
        match name:
            case "boiler":
                if boiler_relay():
                    forced = False
                    boiler_relay('OFF')
                else:
                    forced = True
                    boiler_relay('ON')
                    pygame.time.set_timer(BOILER_OFF, 20*60000, 1)
    else: # short press
        print("Short click on", name)
        match name:
            case "temp":
                display_cur = not display_cur
                if not display_cur:
                    pygame.time.set_timer(TARGET_OFF, 15000,  1)
            case "info":
                if not info:
                    info = True
                    pygame.time.set_timer(INFO_OFF, 30000,  1)
                    pygame.time.set_timer(ANIMATE, anim_dly, 100)

def manage_events():
    global tactile_zones
    global display_cur
    global target_temp
    global mouse_press
    global anim_pct
    global anim_dly
    global cur_temp
    global cur_hum
    global ui_page
    global forced
    global screen
    global info

    # poll for events
    for event in pygame.event.get():
        # pygame.QUIT event means the user clicked X to close your window
        if event.type == pygame.QUIT:
            stop_event.set()
        elif event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.VIDEOEXPOSE, pygame.ACTIVEEVENT]:
            pass
        elif event.type == pygame.FINGERMOTION:
            pass
        elif event.type in [pygame.AUDIODEVICEADDED, pygame.AUDIODEVICEREMOVED]:
            pass
        elif event.type == pygame.FINGERDOWN:
            mouse_press = time_ns()
        elif event.type == pygame.FINGERUP:
            mouse_press = time_ns() - mouse_press
            for zone in tactile_zones:
                if zone.rect.collidepoint((int(event.x * screen.get_width()), int(event.y * screen.get_height()))) and zone.page == ui_page:
                    zone._cb(int(mouse_press/1000000), zone.name)
        elif event.type in [pygame.WINDOWLEAVE, pygame.WINDOWENTER, pygame.WINDOWCLOSE, pygame.WINDOWEXPOSED, pygame.WINDOWSIZECHANGED, pygame.WINDOWSHOWN, pygame.WINDOWHIDDEN, pygame.WINDOWFOCUSGAINED]:
            pass
        elif event.type == MQTT_TICK:
            mqtt.keepalive()
        elif event.type == WDOG_TICK:
            notifier.notify("WATCHDOG=1")
        elif event.type == TEMPO_TICK:
            tempoUpdate()
        elif event.type == TEMP_TICK:
            print("Check for temp")
            now = datetime.now()
            cur_w = now.isoweekday()
            cur_h = now.hour
            cur_m = now.minute

            if sensor:
                buf = "%0.1f°" % sensor.temperature
                cur_temp = buf.replace(".", ",")
                cur_hum  = "%d%%" % int(sensor.relative_humidity)

                for entry in global_vars.boiler_schedule:
                    if entry["weekday"] == cur_w:
                        if (cur_h > entry["start_h"] or
                            (entry["start_h"] == cur_h and cur_m >= entry["start_m"])):
                            target_temp = entry["target_temp"]
                            print("Target temp for schedule starting at %02d:%02d on %d is %0.1f\n", entry["start_h"], entry["start_m"], entry["weekday"], entry["target_temp"])
                            break
                else:
                    target_temp = global_vars.boiler_schedule[-1]["target_temp"]
                if target_temp > sensor.temperature:
                    boiler_relay('ON')
                else:
                    if not forced:
                        boiler_relay('OFF')
        elif event.type == BOILER_OFF:
            forced = False
            boiler_relay('OFF')
        elif event.type == INFO_OFF:
            info = False
            pygame.time.set_timer(ANIMATE, anim_dly, 100)
        elif event.type == ANIMATE:
            if info:
                anim_pct += 1
            else:
                anim_pct -= 1
        elif event.type == TARGET_OFF:
            display_cur = True
        else:
            print("Unknown event %d", event.type)

def run_flask():
    webserver.app.run(debug=False, threaded=True)

# Sync events
stop_event = threading.Event()           # Clean threads shutdown

# GPIO setup
boiler_relay('Init')

# pygame setup
pygame.init()
pygame.font.init()
pygame.mouse.set_visible(False)
if rpi:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode((1024, 600))
clock  = pygame.time.Clock()

# Colors setup
bground_col = pygame.Color(  0,   0,   0)
fground_col = pygame.Color(220, 240, 240)
tempo_r_col = pygame.Color(220,   0,   0)
tempo_w_col = pygame.Color(220, 220, 220)
tempo_b_col = pygame.Color(  0,   0, 220)
tempo_u_col = pygame.Color( 60,  60,  60)
seconds_col = pygame.Color( 11, 156, 215)
bat_dch_col = pygame.Color(225, 142, 233)
bat_chg_col = pygame.Color( 71, 144, 208)
grid_fw_col = pygame.Color(233, 122, 131)
grid_bw_col = pygame.Color(212, 222,  95)
target_col  = pygame.Color(255, 201,  14)
solar_col   = pygame.Color(255, 202,  13)

# Load assets
background    = pygame.image.load('images/background.jpg')
blue_flame    = pygame.image.load('images/blue-flame.png')
grey_flame    = pygame.image.load('images/grey-flame.png')
icon_battery  = pygame.image.load('images/icon-battery.png')
icon_grid     = pygame.image.load('images/icon-grid.png')
icon_solar    = pygame.image.load('images/icon-solar.png')
font_hour     = pygame.font.Font('fonts/Courgette-Regular.ttf', 240)
font_text     = pygame.font.Font('fonts/OpenSans-Medium.ttf', 24)
font_date     = pygame.font.Font('fonts/OpenSans-Medium.ttf', 36)
font_batt     = pygame.font.Font('fonts/OpenSans-Medium.ttf', 50)
font_temp     = pygame.font.Font('fonts/OpenSans-Medium.ttf', 65)
font_hum      = pygame.font.Font('fonts/OpenSans-Medium.ttf', 65)

# Timer events
TEMPO_TICK = pygame.event.custom_type()
TEMP_TICK  = pygame.event.custom_type()
MQTT_TICK  = pygame.event.custom_type()
WDOG_TICK  = pygame.event.custom_type()
BOILER_OFF = pygame.event.custom_type()
INFO_OFF   = pygame.event.custom_type()
ANIMATE    = pygame.event.custom_type()
TARGET_OFF = pygame.event.custom_type()
pygame.time.set_timer(TEMPO_TICK, 120000)
pygame.time.set_timer(MQTT_TICK,   30000)
pygame.time.set_timer(WDOG_TICK,   20000)
pygame.time.set_timer(TEMP_TICK,    3000)
notifier = SystemdNotifier()

# RTE Tempo setup
api_worker = APIWorker(
    client_id="ece3f4f6-b4c0-490c-a79a-23d6795603ed",
    client_secret="1da24e80-1b13-416b-baf9-91a0c652c1a6",
    adjusted_days=False
)
api_worker.start()

mqtt.setup('192.168.0.141', 1883)

tactile_zones = []

signal.signal(signal.SIGINT, signal_handler)

global_vars.init()
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# Flip pygame display on signal
while not stop_event.is_set():
    build_ui()
    manage_events()

api_worker.signalstop("Kiosk shutdown")
mqtt.shutdown()
pygame.quit()
