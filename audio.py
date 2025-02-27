import json
import queue
import signal
import yt_dlp
import pyaudio
import requests
import threading
import subprocess
import global_vars
from PIL import Image
from time import sleep
from io import BytesIO
from ytmusicapi import YTMusic

# ✅ Global variables
BUFFER_THRESHOLD = 10  # Seuil pour déclencher l'événement de lecture audio
BUFFER_MAX_SIZE = 50   # Taille maximale du tampon audio
threads = []           # Ensemble de threads

# ✅ YTMusic initialisation with OAuth
ytmusic = YTMusic('.priv/oauth.json')

# ✅ Buffer queues
q_playlist = queue.Queue()                         # IDs des playlists
q_track    = queue.Queue()                         # Infos des chansons (avec métadonnées)
q_play     = queue.Queue()                         # Infos avec URL audio
q_data     = queue.Queue(maxsize=BUFFER_MAX_SIZE)  # Buffer audio dynamique

# Sync events
stop_event         = threading.Event()   # Clean threads shutdown
next_event         = threading.Event()   # Going to next track
buffer_ready_event = threading.Event()   # Start play when buffer ready

# Global varaibles
bt_present       = False

# ✅ Function : Get best thumbnail
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

# ✅ Function : Download & resize thumbnail
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
    print("Start thread manage_playlist")
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
    print("Start thread manage_track")
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
            '-loglevel', 'error',
            '-hide_banner',
            '-nostats',
            '-'
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
    except Exception as e:
        print(f"Erreur lors du démarrage de la conversion FFmpeg : {e}")
        return None

# ✅ Thread 3 : Traitement de l'audio (lecture des données + mise à jour de l'interface)
def manage_audio():
    global stop_event
    global next_event
    global q_play

    print("Start thread manage_audio")
    while not stop_event.is_set():
        try:
            track_info = q_play.get(timeout=1)
            audio_url = track_info['audio_url']
            next_event.clear()
            
            # ✅ Mise à jour des informations pour l'interface graphique
            global_vars.current_track_info['titre'] = track_info['titre']
            global_vars.current_track_info['artiste'] = track_info['artiste']
            global_vars.current_track_info['album'] = track_info['album']
            global_vars.current_track_info['miniature_url'] = track_info['miniature_url']
            global_vars.current_track_info['miniature'] = load_thumbnail(track_info['miniature_url']) if track_info['miniature_url'] else None
            playing = True

            retries = 3
            process = None
            while retries > 0 and process is None:
                process = convert_audio(audio_url)
                if process is None:
                    retries -= 1
                    sleep(2)

            if process is None:
                print(f"Failed to convert {audio_url}")
                q_play.task_done()
                continue

            buffer_count = 0
            while not stop_event.is_set() and not next_event.is_set():
                if global_vars.current_track_info['playing'] != playing:
                    playing = global_vars.current_track_info['playing']
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
    print("Start thread play_audio")
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

def start_threads():
    global threads

    print("Start threads")
    threads.append(threading.Thread(target=manage_playlist))
    threads.append(threading.Thread(target=manage_track))
    threads.append(threading.Thread(target=manage_audio))
    threads.append(threading.Thread(target=play_audio))

    for thread in threads:
        thread.start()

def stop_threads():
    global threads

    print("Stop threads")
    stop_event.set()
    buffer_ready_event.set()
    while threads:
        threads.pop().join()

if __name__ == "__main__":
    print("Start audio test")
    start_threads()
    sleep(5)
    print("Send playlist")
    q_playlist.put('PLdXUFj15Ms0UsN4vUcqEIlm3VsGb_Re1b')
    sleep(10)
    print("Start play audio")
    global_vars.current_track_info['playing'] = True
    sleep(120)
    print("Next track")
    next_event.set()
    sleep(120)
    print("Pause")
    global_vars.current_track_info['playing'] = False
    sleep(10)
    print("Resume")
    global_vars.current_track_info['playing'] = True
    sleep(120)
    print("Exit")
    stop_threads()
