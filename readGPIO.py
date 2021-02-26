import RPi.GPIO as GPIO ## Import GPIO library
import os
import time
import requests
import sys
import socket
import serial
import fcntl
import struct
import unittest
import subprocess
import inspect
import json
import re
import pymongo

USBDEVFS_RESET= 21780


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.IN)#3G
print("LED 3G GPIO(27)")
print(GPIO.input(27))
       