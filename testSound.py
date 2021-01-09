import pygame
import time
import RPi.GPIO as GPIO ## Import GPIO library


pygame.mixer.init()
pygame.mixer.music.set_volume(float(100)/100)
pygame.mixer.music.load("alert.mp3")
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#========For Sound=========
GPIO.setup(23, GPIO.OUT)#sound
GPIO.output(23,True)#Enable sound

pygame.mixer.music.play()
time.sleep(5)

GPIO.output(23,False)#disable sound
GPIO.cleanup()
print ("Done.\nExiting.")
exit()
