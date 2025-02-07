# ✅ = Généré par IA
import json
import time
import board
import queue
import pygame
import signal
import locale
import yt_dlp
import pyaudio
import requests
import platform
import threading
import subprocess
import pygame.gfxdraw
import subprocess as sp
import paho.mqtt.client as paho
from io import BytesIO
from PIL import Image
from time import strftime, time_ns
from const import FRANCE_TZ
from datetime import datetime
from rtetempo import APIWorker
from ytmusicapi import YTMusic
from dataclasses import dataclass
from adafruit_htu21d import HTU21D
from collections.abc import Callable
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes 

rpi = platform.machine() == "aarch64"
if rpi: import RPi.GPIO as GPIO

# ✅ Shared variables for UI
current_track_info = {
    'titre': 'Titre',
    'artiste': 'Artiste',
    'album': 'Album',
    'miniature_url': None,
    'miniature': None,
    'playing': False
}

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

# ✅ Global variables
BUFFER_THRESHOLD = 10  # Seuil pour déclencher l'événement de lecture audio
BUFFER_MAX_SIZE = 50   # Taille maximale du tampon audio

# Global variables
ydl_opts         = {"geturl": True, "quiet": True}
bt_addr          = "41:42:50:E4:3C:4D"
main_first_run   = True
sched_first_run  = True
info             = False
animate          = False
bt_present       = False
solar_pw         = 0.0
grid_pw          = 0.0
batt_pw          = 0.0
batt_max         = 5000.0
grid_max         = 6800.0
sol_max          = 2920.0
tempo_now        = 'UNKN'
tempo_tmw        = 'UNKN'
cur_batt         = '0,0%'
cur_temp         = '19.0°'
cur_hum          = '45%'
ui_page          = 'main'
gauge_h          = 80
anim_pct         = 0
anim_dly         = 5
audio_cnt        = 0

# ✅ Fonction : Get best thumbnail
def get_best_thumbnail(thumbnails):
    square_thumbnails = [
        t for t in thumbnails if t.get('width') == t.get('height') and t['width'] <= 160
    ]
    if square_thumbnails:
        return max(square_thumbnails, key=lambda t: t['width'])['url']
    
    closest_thumbnail = min(
        thumbnails,
        key=lambda t: abs(max(t.get('width', 0), t.get('height', 0)) - 160)
    )
    return closest_thumbnail['url']

# ✅ Download & resize thumbnail
def load_thumbnail(url):
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img = img.resize((160, 160))
        return pygame.image.fromstring(img.tobytes(), img.size, img.mode)
    except:
        return None

# ✅ Thread 1 : Manage playlists
def manage_playlist():
    while not stop_event.is_set():
        try:
            playlist_id = q_playlist.get(timeout=1)
            playlist = ytmusic.get_playlist(playlist_id, limit=None)
            for track in playlist.get('tracks', []):
                thumbnails = track.get('thumbnails', [])
                miniature_url = get_best_thumbnail(thumbnails) if thumbnails else None

                info_track = {
                    'titre': track.get('title', 'Inconnu'),
                    'artiste': track['artists'][0]['name'] if track.get('artists') else 'Inconnu',
                    'album': track['album']['name'] if track.get('album') else 'Inconnu',
                    'miniature_url': miniature_url,
                    'id_youtube': track.get('videoId', 'Inconnu')
                }
                print("Add new track")
                print(info_track)
                q_track.put(info_track)
            q_playlist.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Erreur lors du traitement de la playlist {playlist_id} : {e}")
            q_playlist.task_done()

# ✅ Thread 2 : Extract audio stream URL
def manage_track():
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'format': 'bestaudio/best'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        while not stop_event.is_set():
            try:
                track_info = q_track.get(timeout=1)
                video_id = track_info['id_youtube']
                if video_id:
                    url = f"https://www.youtube.com/watch?v={video_id}"
                else:
                    print("Invalid youtube Id")
                    q_track.task_done()
                    continue

                data = ydl.extract_info(url, download=False)
                audio_url = data['url'] if 'url' in data else None
                track_info['audio_url'] = audio_url

                q_play.put(track_info)
                q_track.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Erreur lors de l'extraction audio pour {video_id} : {e}")
                q_track.task_done()

# ✅ Fonction : Convert audio using ffmpeg
def convert_audio(audio_url):
    try:
        cmd = [
            'ffmpeg',
            '-i', audio_url,
            '-f', 's16le',
            '-acodec', 'pcm_s16le',
            '-ac', '2',
            '-ar', '44100',
            '-'
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
    except Exception as e:
        print(f"Erreur lors du démarrage de la conversion FFmpeg : {e}")
        return None

# ✅ Thread 3 : Traitement de l'audio (lecture des données + mise à jour de l'interface)
def manage_audio():
    while not stop_event.is_set():
        try:
            track_info = q_play.get(timeout=1)
            audio_url = track_info['audio_url']
            next_event.clear()
            
            # ✅ Mise à jour des informations pour l'interface graphique
            current_track_info['titre'] = track_info['titre']
            current_track_info['artiste'] = track_info['artiste']
            current_track_info['album'] = track_info['album']
            current_track_info['miniature_url'] = track_info['miniature_url']
            current_track_info['miniature'] = load_thumbnail(track_info['miniature_url']) if track_info['miniature_url'] else None
            current_track_info['playing'] = True
            playing = True

            retries = 3
            process = None
            while retries > 0 and process is None:
                process = convert_audio(audio_url)
                if process is None:
                    retries -= 1
                    time.sleep(2)

            if process is None:
                print(f"Failed to convert {audio_url}")
                q_play.task_done()
                continue

            buffer_count = 0
            while not stop_event.is_set() and not next_event.is_set():
                if current_track_info['playing'] != playing:
                    playing = current_track_info['playing']
                    if playing:
                        process.send_signal(18) # SIGCONT
                    else:
                        process.send_signal(19) # SIGSTOP
                if playing:
                    data = process.stdout.read(4096)
                    if not data:
                        break

                    try:
                        q_data.put(data, timeout=1)
                        buffer_count += 1
                        if buffer_count == BUFFER_THRESHOLD and not buffer_ready_event.is_set():
                            print("Buffer filled")
                            buffer_ready_event.set()
                    except queue.Full:
                        print("Buffer overflow")
                        continue

            q_data.put(None)
            process.kill()

            stderr_output = process.stderr.read().decode()
            if stderr_output:
                print(f"Erreur FFmpeg : {stderr_output}")

            process.stdout.close()
            process.stderr.close()
            process.wait()
            q_play.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Audio error : {e}")
            q_play.task_done()

# ✅ Thread 4 : Lecture audio avec PyAudio
def play_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=2, rate=44100, output=True)

    while not stop_event.is_set():
        print("Waiting buffer for next track...")
        buffer_ready_event.wait()
        buffer_ready_event.clear()
        print("Buffer ready, play audio.")

        while not stop_event.is_set():
            try:
                data = q_data.get(timeout=1)
                if data is None:
                    print("End of track detected.")
                    q_data.task_done()
                    break

                stream.write(data)
                q_data.task_done()
            except queue.Empty:
                continue

    while not q_data.empty():
        q_data.get()
        q_data.task_done()

    stream.stop_stream()
    stream.close()
    p.terminate()

def boiler_relay(cmd = "Query"):
    if not rpi:
        return False
    if cmd == 'Init':
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(9, GPIO.OUT)
        GPIO.output(9, GPIO.LOW)
    if cmd == 'OFF':
        GPIO.output(9, GPIO.LOW)
    if cmd == 'ON':
        GPIO.output(9, GPIO.HIGH)
    return GPIO.input(9)

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
def buildSchedUI():
    global sched_first_run

    screen.blit(background, (0, 0))
    sched_first_run = False

# Redraw main screen
def buildMainUI():
    global info
    global cur_hum
    global grid_pw
    global batt_pw
    global solar_pw
    global anim_pct
    global cur_batt
    global cur_temp
    global tempo_now
    global tempo_tmw
    global main_first_run
    global tactile_zones
    global current_track_info

    cur_time = strftime('%H:%M')
    cur_date = strftime('%A ') + strftime('%d').lstrip('0') + strftime(' %B %Y')

    screen.blit(background, (0, 0))

    tempoDraw(tempo_now, (863, 63), 17)
    tempoDraw(tempo_tmw, (900, 67), 13)
    r = pygame.Rect(699 - anim_pct, 112, 269 + anim_pct, 432)
    pygame.draw.rect(screen, fground_col, r, 2, 33)
    if main_first_run:
        tactile_zones.append(TactileZone(click_main, r, "info", "main"))
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
    if boiler_relay():
        screen.blit(blue_flame, (275, 50))
    else:
        screen.blit(grey_flame, (275, 50))
    screen.blit(icon_solar,     (830, 138))
    screen.blit(icon_grid,      (830, 251))
    screen.blit(icon_battery,   (830, 361))
    if bt_present:
        if current_track_info.get('playing'):
            img = pause
        else:
            img = play_enabled
    else:
        img = play_disabled
    r = screen.blit(img , (225, 453))
    if main_first_run:
        tactile_zones.append(TactileZone(click_main, r, "play", "main"))
    if bt_present:
        img = next_enabled
    else:
        img = next_disabled
    r = screen.blit(img,  (322, 453))
    if main_first_run:
        tactile_zones.append(TactileZone(click_main, r, "next", "main"))
    if bt_present:
        img = bt_enabled
    else:
        img = bt_disabled
    r = screen.blit(img, (427, 453))
    if main_first_run:
        tactile_zones.append(TactileZone(click_main, r, "bt", "main"))
    albumart = current_track_info.get('miniature')
    if not albumart:
        albumart = audio_wait
    r = screen.blit(albumart, (20, 400))
    if main_first_run:
        tactile_zones.append(TactileZone(click_main, r, "playlist", "main"))
    main_first_run = False

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
    stop_event.set()

def click_main(duration_ms, name):
    global info

    if duration_ms > 1000: # very long press
        print("Very long click on", name)
    elif duration_ms > 150: # long press
        print("Long click on", name)
        match name:
            case "boiler":
                if boiler_relay():
                    boiler_relay('OFF')
                else:
                    boiler_relay('ON')
                    pygame.time.set_timer(BOILER_OFF, 20*60000, 1)
    else: # short press
        print("Short click on", name)
        match name:
            case "play":
                current_track_info['playing'] = not current_track_info['playing']
            case "next":
                next_event.set()
            case "info":
                if not info:
                    info = True
                    pygame.time.set_timer(INFO_OFF, 30000,  1)
                    pygame.time.set_timer(ANIMATE, anim_dly, 100)

def manage_events():
    global tactile_zones
    global mouse_press
    global bt_present
    global properties
    global anim_pct
    global anim_dly
    global cur_temp
    global cur_hum
    global ui_page
    global bt_addr
    global client
    global sensor
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
            client.publish('R/d83add91edfc/keepalive','{ "keepalive-options" : ["suppress-republish"] }', 2, properties=properties)
        elif event.type == TEMPO_TICK:
            tempoUpdate()
        elif event.type == TEMP_TICK:
            bt_present = bt_addr in sp.getoutput("hcitool con").split()
            if sensor:
                buf = "%0.1f°" % sensor.temperature
                cur_temp = buf.replace(".", ",")
                cur_hum  = "%d%%" % int(sensor.relative_humidity)
        elif event.type == BOILER_OFF:
            boiler_relay('OFF')
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

# ✅ YTMusic initialisation with OAuth
ytmusic = YTMusic('.priv/oauth.json')

# ✅ Files tampons
q_playlist = queue.Queue()               # IDs des playlists
q_track = queue.Queue()                  # Infos des chansons (avec métadonnées)
q_play = queue.Queue()                   # Infos avec URL audio
q_data = queue.Queue(maxsize=BUFFER_MAX_SIZE)  # Buffer audio dynamique

# Sync events
stop_event = threading.Event()           # Clean threads shutdown
next_event = threading.Event()           # Going to next track
buffer_ready_event = threading.Event()   # Start play when buffer ready

# GPIO setup
boiler_relay('Init')

# Temperature sensor setup
if rpi:
    i2c = board.I2C()  # uses board.SCL and board.SDA
    sensor = HTU21D(i2c)
else:
    sensor = None

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
audio_wait    = pygame.image.load('images/audio_wait.jpg')
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

tactile_zones = []
tactile_zones.append(TactileZone(click_main, pygame.Rect(270,  35,  48,  70), "boiler", "main"))

signal.signal(signal.SIGINT, signal_handler)

# Start threads
threads = []
#threads.append(threading.Thread(target=manage_playlist))
#threads.append(threading.Thread(target=manage_track))
#threads.append(threading.Thread(target=manage_audio))
#threads.append(threading.Thread(target=play_audio))
threads.append(threading.Thread(target=build_ui))
threads.append(threading.Thread(target=manage_events))

for thread in threads:
  thread.start()

# ✅ Exemple d'ajout d'une playlist à traiter
#q_playlist.put('PLdXUFj15Ms0UsN4vUcqEIlm3VsGb_Re1b')  # Remplacer par un ID réel

# Flip pygame display on signal
while not stop_event.is_set():
    build_ui()
    manage_events()

# Shutdown threads
buffer_ready_event.set()
while threads:
  threads.pop().join()

api_worker.signalstop("Kiosk shutdown")
client.loop_stop()
client.disconnect()
pygame.quit()
