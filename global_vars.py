import os
import json

schedule_file = '.priv/schedule.json'
current_track_info = {
    'titre': 'Titre',
    'artiste': 'Artiste',
    'album': 'Album',
    'miniature_url': None,
    'miniature': None,
    'playing': False
}
boiler_schedule = [
        {"weekday": 1, "start_h":  5, "start_m": 45, "target_temp": 19.0},
        {"weekday": 1, "start_h":  8, "start_m":  0, "target_temp": 18.0},
        {"weekday": 1, "start_h": 11, "start_m": 45, "target_temp": 19.0},
        {"weekday": 1, "start_h": 13, "start_m":  0, "target_temp": 18.0},
        {"weekday": 1, "start_h": 15, "start_m": 45, "target_temp": 19.5},
        {"weekday": 1, "start_h": 22, "start_m": 15, "target_temp": 17.5},
        {"weekday": 2, "start_h":  5, "start_m": 45, "target_temp": 19.0},
        {"weekday": 2, "start_h":  8, "start_m":  0, "target_temp": 18.0},
        {"weekday": 2, "start_h": 11, "start_m": 45, "target_temp": 19.0},
        {"weekday": 2, "start_h": 13, "start_m":  0, "target_temp": 18.0},
        {"weekday": 2, "start_h": 15, "start_m": 45, "target_temp": 19.5},
        {"weekday": 2, "start_h": 22, "start_m": 15, "target_temp": 17.5},
        {"weekday": 3, "start_h":  5, "start_m": 45, "target_temp": 19.0},
        {"weekday": 3, "start_h":  8, "start_m":  0, "target_temp": 18.0},
        {"weekday": 3, "start_h": 11, "start_m": 45, "target_temp": 19.0},
        {"weekday": 3, "start_h": 13, "start_m":  0, "target_temp": 18.0},
        {"weekday": 3, "start_h": 15, "start_m": 45, "target_temp": 19.5},
        {"weekday": 3, "start_h": 22, "start_m": 15, "target_temp": 17.5},
        {"weekday": 4, "start_h":  5, "start_m": 45, "target_temp": 19.0},
        {"weekday": 4, "start_h":  8, "start_m":  0, "target_temp": 18.0},
        {"weekday": 4, "start_h": 11, "start_m": 45, "target_temp": 19.0},
        {"weekday": 4, "start_h": 13, "start_m":  0, "target_temp": 18.0},
        {"weekday": 4, "start_h": 15, "start_m": 45, "target_temp": 19.5},
        {"weekday": 4, "start_h": 22, "start_m": 15, "target_temp": 17.5},
        {"weekday": 5, "start_h":  5, "start_m": 45, "target_temp": 19.0},
        {"weekday": 5, "start_h":  8, "start_m":  0, "target_temp": 18.0},
        {"weekday": 5, "start_h": 11, "start_m": 45, "target_temp": 19.0},
        {"weekday": 5, "start_h": 13, "start_m":  0, "target_temp": 18.0},
        {"weekday": 5, "start_h": 15, "start_m": 45, "target_temp": 19.5},
        {"weekday": 5, "start_h": 22, "start_m": 15, "target_temp": 17.5},
        {"weekday": 6, "start_h":  5, "start_m": 45, "target_temp": 19.0},
        {"weekday": 6, "start_h": 22, "start_m": 15, "target_temp": 17.5},
        {"weekday": 0, "start_h":  5, "start_m": 45, "target_temp": 19.0},
        {"weekday": 0, "start_h": 22, "start_m": 15, "target_temp": 17.5},
]

def save_schedule():
    global boiler_schedule

    with open(schedule_file, 'w', encoding='utf-8') as file:
        json.dump(boiler_schedule, file, ensure_ascii=False, indent=4)

def init():
    global boiler_schedule

    if not os.path.exists(schedule_file):
        save_schedule()
    with open(schedule_file, 'r', encoding='utf-8') as file:
        boiler_schedule = json.load(file)
