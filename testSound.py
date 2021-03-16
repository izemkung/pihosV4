
import time
import RPi.GPIO as GPIO ## Import GPIO library

import vlc
player = vlc.MediaPlayer("alert.mp3")



GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#========For Sound=========
GPIO.setup(23, GPIO.OUT)#sound
GPIO.output(23,True)#Enable sound

player.audio_set_volume(50)
time.sleep(0.5)
player = vlc.MediaPlayer("alert.mp3")
player.play()
time.sleep(0.5)
duration = player.get_length() / 1000
time.sleep(duration - 2)

player.audio_set_volume(100)
time.sleep(0.5)
player = vlc.MediaPlayer("alert.mp3")
player.play()
time.sleep(0.5)
duration = player.get_length() / 1000
time.sleep(duration - 2)

GPIO.output(23,False)#disable sound
GPIO.cleanup()
print ("Done.\nExiting.")
exit()
