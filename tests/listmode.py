import pygame
import os

pygame.init()
print("Driver utilisé :", pygame.display.get_driver())

available_drivers = ["fbcon", "directfb", "kmsdrm", "rpi", "x11"]
for driver in available_drivers:
    os.environ["SDL_VIDEODRIVER"] = driver
    try:
        pygame.display.init()
        print(f"Driver {driver} fonctionne !")
        pygame.display.quit()
    except pygame.error:
        print(f"Driver {driver} non disponible.")

