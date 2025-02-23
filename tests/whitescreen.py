import pygame
import sys

# Initialiser Pygame
pygame.init()
print(pygame.ver)

# Créer une fenêtre en plein écran
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption('Fenêtre Blanche Plein Écran')

# Remplir l'écran avec du blanc
screen.fill((255, 255, 255))

# Mettre à jour l'affichage
pygame.display.flip()

pygame.time.wait(5000)

pygame.quit()
sys.exit()
