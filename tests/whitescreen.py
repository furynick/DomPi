import os
import pygame

os.environ["SDL_VIDEODRIVER"] = "fbcon"
os.environ["SDL_FBDEV"] = "/dev/fb0"

pygame.init()
screen = pygame.display.set_mode((320, 240))  # Taille plus petite pour tester

screen.fill((255, 255, 255))
pygame.display.flip()

pygame.time.wait(5000)
pygame.quit()
