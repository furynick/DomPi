import os
import pygame

os.environ["SDL_VIDEODRIVER"] = "kmsdrm"
os.environ["SDL_FBDEV"] = "/dev/fb0"

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

screen.fill((255, 255, 255))
pygame.display.flip()

pygame.time.wait(5000)
pygame.quit()
