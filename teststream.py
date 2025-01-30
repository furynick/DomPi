import vlc
import yt_dlp
import sys

def pprint(web, level=0):
    for k,v in web.items():
        if isinstance(v, dict):
            print('\t'*level, f'{k}: ')
            level += 1
            pprint(v, level)
            level -= 1
        else:
            print('\t'*level, k, ": ", v)

yt_url   = 'https://www.youtube.com/watch?v=bXr-9tWhefo'
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
for thumbnail in info["thumbnails"]:
    if "height" not in thumbnail.keys():
        continue
    if thumbnail["height"] != thumbnail["width"]:
        continue
    if thumbnail["height"] >= size:
        continue
    size    = thumbnail["height"]
    art_url = thumbnail["url"]
print(art_url)

p = vlc.MediaPlayer(audio_url)
p.play()
input("press enter to quit")
p.stop()
