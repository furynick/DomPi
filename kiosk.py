import pygame
import pygame.gfxdraw
from time import sleep, strftime, time_ns
from datetime import datetime
from rtetempo import APIWorker
from const import FRANCE_TZ

# pygame setup
pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((1024, 600))
clock = pygame.time.Clock()

# Colors setup
bground_col   = pygame.Color(  0,   0,   0)
tempo_r_col = pygame.Color(220,   0,   0)
tempo_w_col = pygame.Color(220, 220, 220)
tempo_b_col = pygame.Color(  0,   0, 220)
tempo_u_col = pygame.Color( 60,  60,  60)
seconds_col = pygame.Color( 11, 156, 215)

# Timer events
TEMPO_TICK = pygame.event.custom_type()
HALF_TICK = pygame.event.custom_type()
pygame.time.set_timer(TEMPO_TICK, 120000)
pygame.time.set_timer(HALF_TICK, 500)

# RTE Tempo setup
api_worker = APIWorker(
    client_id="ece3f4f6-b4c0-490c-a79a-23d6795603ed",
    client_secret="1da24e80-1b13-416b-baf9-91a0c652c1a6",
    adjusted_days=False
)
api_worker.start()

# Load assets
blue_flame = pygame.image.load('blue-flame.png')
grey_flame = pygame.image.load('grey-flame.png')
font_date  = pygame.font.SysFont('ubuntu', 28)
font_hour  = pygame.font.SysFont('sourcesanspro', 200)
font_temp  = pygame.font.SysFont('ubuntu', 70)
font_text  = pygame.font.SysFont('ubuntucondensed', 80)

# Global variables
running = True
cur_time = '66:66'
cur_date = ''
cur_temp = '18,3°'
tempo_now = 'UNKN'
tempo_tmw = 'UNKN'

def tempoDraw(state, c):
    col = tempo_u_col
    match state:
        case 'BLUE':
            col = tempo_b_col
        case 'WHITE':
            col = tempo_w_col
        case 'RED':
            col = tempo_r_col
            
    pygame.gfxdraw.aacircle(screen, c[0], c[1], 31, col)
    pygame.gfxdraw.filled_circle(screen, c[0], c[1], 30, col)
    pygame.gfxdraw.aacircle(screen, c[0], c[1], 31, bground_col)

# Redraw full screen function
def redraw():
    global tempo_now
    global tempo_tmw

    screen.fill(bground_col)
    date_srf = font_date.render(cur_date, True, "white", None)
    temp_srf = font_temp.render(cur_temp, True, "white", None)
    hour_srf = font_hour.render(cur_time, True, "white", None)
    date_crd = date_srf.get_rect()
    date_crd.center = (300, 200)
    hour_crd = hour_srf.get_rect()
    hour_crd.center = (300, 300)
    temp_crd = temp_srf.get_rect()
    temp_crd.center = (512,  35)
    
    tempoDraw(tempo_tmw, (95, 40))
    tempoDraw(tempo_now, (45, 40))
    
    # build clock
    dt = datetime.now()
    for r in range(257, 260):
        pygame.gfxdraw.arc(screen, 300, 300, r, -90, int(6*(dt.second+dt.microsecond/1000000))-89, seconds_col)
#    pygame.gfxdraw.aacircle(screen, 300, 300, 265, bground_col)
#    pygame.gfxdraw.filled_circle(screen, 300, 300, 265, bground_col)

    screen.blit(hour_srf,   hour_crd)
    screen.blit(date_srf,   date_crd)
    screen.blit(blue_flame, ( 20, 480))
    screen.blit(temp_srf,   temp_crd)
    pygame.display.flip()

def tempoUpdate():
    global tempo_now
    global tempo_tmw

    tempo_now = 'UNKN'
    tempo_tmw = 'UNKN'
    localized_now = datetime.now(FRANCE_TZ)
    t = api_worker.get_adjusted_days()
    for tempo_day in t:
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
        match event.type:
            # pygame.QUIT event means the user clicked X to close your window
            case pygame.QUIT:
                running = False
            case TEMPO_TICK:
                tempoUpdate()

    cur_time = strftime('%H:%M')
    cur_date = strftime('%A %-d %B %Y')
    redraw()
    
    t = api_worker.get_adjusted_days()
    if t != [] and track_tempo:
        print(tempoUpdate())
        track_tempo = False

api_worker.signalstop("Kiosk shutdown")
pygame.quit()
