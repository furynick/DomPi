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

def dump(obj, nested_level=0, output=sys.stdout):
    spacing = '   '
    if isinstance(obj, dict):
        print >> output, '%s{' % ((nested_level) * spacing)
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print >> output, '%s%s:' % ((nested_level + 1) * spacing, k)
                dump(v, nested_level + 1, output)
            else:
                print >> output, '%s%s: %s' % ((nested_level + 1) * spacing, k, v)
        print >> output, '%s}' % (nested_level * spacing)
    elif isinstance(obj, list):
        print >> output, '%s[' % ((nested_level) * spacing)
        for v in obj:
            if hasattr(v, '__iter__'):
                dump(v, nested_level + 1, output)
            else:
                print >> output, '%s%s' % ((nested_level + 1) * spacing, v)
        print >> output, '%s]' % ((nested_level) * spacing)
    else:
        print >> output, '%s%s' % (nested_level * spacing, obj)

yt_url   = 'https://www.youtube.com/watch?v=bXr-9tWhefo'
ydl_opts = {"geturl": True, "quiet": True}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(yt_url, download=False)
print(info["title"])
size = 8192
for thumbnail in info["thumbnails"]:
    if thumbnail["height"] != thumbnail["width"]:
        continue
    if thumbnail["height"] >= size:
        continue
    size    = thumbnail["height"]
    art_url = thumbnail["url"]
print(art_url)

p = vlc.MediaPlayer(info["requested_formats"][1]["url"])
p.play()
input("press enter to quit")
p.stop()
