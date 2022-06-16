#!/usr/bin/env python3
#
# Game to estimate PI
#

import sys
import pygame
import pygame.camera

pygame.camera.init()
pygame.camera.list_cameras() #Camera detected or not

size = (640,480)
display = pygame.display.set_mode(size, 0)
cam = pygame.camera.Camera("/dev/video0", size)
cam.start()

thresholded = pygame.surface.Surface(size, 0, display)
snapshot = cam.get_image()
pygame.transform.threshold(thresholded,snapshot,(0,255,0),
    threshold = (90,170,170),
    set_color = (0,0,0),
    set_behavior = 1
)

# thresholded = pygame.surface.Surface(size, 0, display)
# snapshot = cam.get_image()
# pygame.transform.threshold(thresholded,snapshot,(0,255,0),(30,30,30),(0,0,0),1,self.background)
pygame.image.save(snapshot,"filename.jpg")
