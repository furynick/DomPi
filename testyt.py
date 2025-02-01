import queue
import yt_dlp
import pyaudio
import threading
import requests
import subprocess
from ytmusicapi import YTMusic

# 🔊 Détection de l'ID de la carte ALSA "bluealsa" avec PyAudio
def get_bluealsa_card_id():
    p = pyaudio.PyAudio()
    bluealsa_card_id = None

    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        name = device_info.get('name', '').lower()

        if 'bluealsa' in name:
            bluealsa_card_id = device_info['index']
            print(f"Carte ALSA 'bluealsa' détectée avec l'ID : {bluealsa_card_id}")
            break

    if bluealsa_card_id is None:
        print("Carte ALSA 'bluealsa' non détectée.")

    p.terminate()
    return bluealsa_card_id

# Détection de la carte bluealsa au démarrage
bluealsa_card_id = get_bluealsa_card_id()

# Files de communication entre les threads
song_queue = queue.Queue()
audio_queue = queue.Queue()

# Événement d'arrêt pour la gestion des threads
stop_event = threading.Event()

# Récupérer l'ID de la dernière chanson traitée
def get_last_processed_video_id():
    try:
        with open('last_processed_song.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

# Enregistrer l'ID de la dernière chanson traitée
def save_last_processed_video_id(video_id):
    with open('last_processed_song.txt', 'w') as f:
        f.write(video_id)

def fetch_playlist(playlist_id, song_queue, stop_event, last_video_id):
    ytmusic = YTMusic('.priv/yt_music.headers.json')
    playlist = ytmusic.get_playlist(playlist_id, limit=255)
    skip = last_video_id is not None

    for track in playlist['tracks']:
        if stop_event.is_set():
            break

        video_id = track.get('videoId')
        if not video_id:
            continue

        if skip:
            if video_id == last_video_id:
                skip = False  # Reprendre à partir de la chanson suivante
            continue

        song_info = {
            'title': track['title'],
            'artist': track['artists'][0]['name'],
            'videoId': video_id
        }
        song_queue.put(song_info)
    song_queue.put(None)  # Marqueur de fin

# 🔊 Tâche de conversion audio avec FFmpeg
def audio_converter(stream_url, audio_queue, stop_event):
    ffprobe_cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'a:0',
        '-show_entries', 'stream=sample_rate,channels',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        stream_url
    ]

    try:
        result = subprocess.run(ffprobe_cmd, capture_output=True, text=True)
        sample_rate, channels = map(int, result.stdout.strip().split('\n'))
        sample_rate = 44100

        ffmpeg_cmd = [
            'ffmpeg',
            '-i', stream_url,
            '-f', 's16le',  # PCM 16 bits little endian
            '-acodec', 'pcm_s16le',
            '-ac', str(channels),
            '-ar', str(sample_rate),
            '-'
        ]

        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        while not stop_event.is_set():
            buffer = process.stdout.read(4096)
            if not buffer:
                break
            audio_queue.put((buffer, sample_rate, channels))

        process.terminate()
    except Exception as e:
        print(f"Erreur de conversion audio : {e}")

# 🔊 Fonction pour lire le flux audio depuis la file audio
def play_audio_stream(audio_queue, stop_event):
    p = pyaudio.PyAudio()
    audio_stream = None

    try:
        while not stop_event.is_set():
            item = audio_queue.get()
            if item is None:
                break

            buffer, sample_rate, channels = item

            if audio_stream is None:
                audio_stream = p.open(
                    format=pyaudio.paInt16,
                    channels=channels,
                    rate=sample_rate,
                    output=True,
                    output_device_index=bluealsa_card_id  # Utilisation de la carte bluealsa
                )

            audio_stream.write(buffer)
            audio_queue.task_done()

        if audio_stream:
            audio_stream.stop_stream()
            audio_stream.close()
    finally:
        p.terminate()

def process_songs(song_queue, audio_queue, stop_event):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        while not stop_event.is_set():
            song = song_queue.get()

            if song is None:
                song_queue.task_done()
                audio_queue.put(None)  # Indiquer la fin de l'audio
                break

            video_id = song.get('videoId')
            if not video_id:
                song_queue.task_done()
                continue

            try:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

                audio_formats = [f for f in info.get('formats', []) if f.get('acodec') != 'none' and f.get('vcodec') == 'none' and f.get('abr')]
                if audio_formats:
                    best_audio = max(audio_formats, key=lambda f: f['abr'])
                    stream_url = best_audio.get('url')
                    bitrate_kbps = round(best_audio.get('abr'))
                else:
                    stream_url = None
                    bitrate_kbps = 0

                print(f"Ajout de : {song['title']} par {song['artist']}")
                print(f"URL du flux : {stream_url if stream_url else 'Non disponible'}")
                print(f"Débit : {bitrate_kbps} kbps")

                if stream_url:
                    converter_thread = threading.Thread(target=audio_converter, args=(stream_url, audio_queue, stop_event))
                    converter_thread.start()
                    converter_thread.join()

            except Exception as e:
                print(f"Erreur lors de l'extraction de {song['title']}: {e}")
            finally:
                song_queue.task_done()

# ID de la playlist
playlist_id = 'PLdXUFj15Ms0UsN4vUcqEIlm3VsGb_Re1b'

# Dernière chanson traitée
last_video_id = get_last_processed_video_id()

# Threads
fetch_thread = threading.Thread(target=fetch_playlist, args=(playlist_id, song_queue, stop_event, last_video_id))
process_thread = threading.Thread(target=process_songs, args=(song_queue, audio_queue, stop_event))
play_thread = threading.Thread(target=play_audio_stream, args=(audio_queue, stop_event))

# Lancement des threads
fetch_thread.start()
process_thread.start()
play_thread.start()

try:
    fetch_thread.join()
    song_queue.join()
    audio_queue.join()
except KeyboardInterrupt:
    print("Arrêt du programme par l'utilisateur.")
    stop_event.set()
    fetch_thread.join()
    process_thread.join()
    play_thread.join()

