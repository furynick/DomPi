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

# Attendre qu'une touche soit pressée
print("Appuyez sur une touche pour quitter...")
while True:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            pygame.quit()
            sys.exit()
