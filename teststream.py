import os
import threading
import yt_dlp
import sys
import subprocess
import requests
import asyncio
import subprocess
import pyaudio
import queue
from aioprocessing import AioProcess

def pprint(web, level=0):
    for k,v in web.items():
        if isinstance(v, dict):
            print('\t'*level, f'{k}: ')
            level += 1
            pprint(v, level)
            level -= 1
        else:
            print('\t'*level, k, ": ", v)

yt_url   = 'https://www.youtube.com/watch?v=u08B6Fbw9oQ'
ydl_opts = {"geturl": True, "quiet": True}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(yt_url, download=False)
print(info["title"])

abr = 0.0
for track in info["formats"]:
    if track["resolution"] != "audio only" or track["abr"] == None:
        continue
    if float(track["abr"]) > abr:
        abr = track["abr"]
        audio_url = track["url"]
print(audio_url)

size = 8192
art_url = ""
for thumbnail in info["thumbnails"]:
    if "height" not in thumbnail.keys():
        continue
    if thumbnail["height"] != thumbnail["width"]:
        continue
    if thumbnail["height"] >= size:
        continue
    size    = thumbnail["height"]
    art_url = thumbnail["url"]
if art_url != "":
    print(art_url)
else:
    print("No thumbnail")

# PyAudio parameters
SAMPLE_RATE = 44100
CHANNELS = 2
CHUNK_SIZE = 32768

# Global play control
is_playing = True

# Initialize PyAudio
p = pyaudio.PyAudio()
audio_queue = queue.Queue(maxsize=10)  # Tampon de 10 paquets
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['name'] == "bluealsa":
        stream = p.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            output=True,
            output_device_index=i,
            frames_per_buffer=CHUNK_SIZE
        )

async def start_ffmpeg():
    """ Start ffmpeg with real-time low-latency settings """
    env = os.environ.copy()
    env["AUDIODEV"] = "hw:0,0"  # Direct ALSA output, adjust if needed

    return await asyncio.create_subprocess_exec(
        "ffmpeg", "-re", "-i", audio_url,
        "-f", "s16le", "-ac", str(CHANNELS), "-ar", str(SAMPLE_RATE),
        "-fflags", "nobuffer", "-flags", "low_delay",
        "-probesize", "32", "-analyzeduration", "0",
        "-flush_packets", "1", "-bufsize", "64k",  # Réduction de la taille du buffer
        "-loglevel", "info",               # Enable logging
        "pipe:1",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )

async def stream_audio():
    """ Async function to stream and play audio with minimal delay """
    global is_playing
    process = await start_ffmpeg()

    async def log_ffmpeg_output():
        """ Read ffmpeg logs asynchronously """
        while True:
            log_line = await process.stderr.readline()
            if not log_line:
                break
            print(f"FFMPEG LOG: {log_line.decode().strip()}")

    async def read_ffmpeg_output():
        """ Read ffmpeg data asynchronously """
        global is_playing

    asyncio.create_task(log_ffmpeg_output())  # Start log reader
    asyncio.create_task(read_ffmpeg_output())  # Start data reader

    while True:
        try:
            if not is_playing:
                await asyncio.sleep(0.1)  # Pause loop
                continue

            audio_chunk = await process.stdout.read(CHUNK_SIZE * 2 * CHANNELS)

            if not audio_chunk:  # Song ended (EOF)
                print("Playback finished.")
                break  # Exit gracefully

            stream.write(audio_chunk)  # Non-blocking audio playback

        except Exception as e:
            print(f"Error: {e}. Stopping playback.")
            break  # Stop on unexpected errors

    # Cleanup when playback ends
    process.terminate()
    await process.wait()

def run_async_main():
    """ Run asyncio event loop inside a thread """
    asyncio.run(stream_audio())

# Start the async loop in a thread
stream_thread = threading.Thread(target=run_async_main, daemon=True)
stream_thread.start()

def toggle_play_pause():
    """ Toggle play/pause """
    global is_playing
    is_playing = not is_playing
    print("Paused" if not is_playing else "Resumed")

# Command loop
print("Streaming started! Commands: [p]ause/[r]esume, [q]uit")
while True:
    command = input("> ").strip().lower()
    
    if command == "p" or command == "r":
        toggle_play_pause()
    elif command == "q":
        break

# Cleanup
stream_thread.join()
stream.stop_stream()
stream.close()
p.terminate()
