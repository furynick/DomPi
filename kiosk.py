import pygame
import pygame.gfxdraw
from time import sleep, strftime, time_ns
from datetime import datetime

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
HALF_TICK = pygame.event.custom_type()
pygame.time.set_timer(HALF_TICK, 500)   

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
tempo_day = 2
tempo_tmw = 0

def tempoDraw(state, c):
    match state:
        case 0:
            col = tempo_u_col
        case 1:
            col = tempo_b_col
        case 2:
            col = tempo_w_col
        case 3:
            col = tempo_r_col
            
    pygame.gfxdraw.aacircle(screen, c[0], c[1], 30, col)
    pygame.gfxdraw.filled_circle(screen, c[0], c[1], 30, col)

    
# Redraw full screen function
def redraw():
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
    
    tempoDraw(0, (95, 40))
    tempoDraw(3, (45, 40))
    
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

# Main loop
while running:
    # limit to 60fps to prevent CPU overload
    clock.tick(60)

    # poll for events
    for event in pygame.event.get():
        match event.type:
            # pygame.QUIT event means the user clicked X to close your window
            case pygame.QUIT:
                running = False

    cur_time = strftime('%H:%M')
    cur_date = strftime('%A %-d %B %Y')
    redraw()

pygame.quit()
