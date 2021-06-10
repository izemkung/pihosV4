
import RPi.GPIO as GPIO ## Import GPIO library
import time


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(22, GPIO.OUT)#GPS
GPIO.setup(17, GPIO.OUT)#VDO

while(True):
    GPIO.output(22,True)
    time.sleep(1)
    GPIO.output(22,False)
    time.sleep(1)
    GPIO.output(17,True)
    time.sleep(1)
    GPIO.output(17,False)
    time.sleep(1)  