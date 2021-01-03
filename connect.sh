cd /
cd home/pi/3g
sudo /home/pi/3g/umtskeeper --sakisoperators "USBINTERFACE='3' OTHER='USBMODEM' USBMODEM='05c6:9003' APN="CUSTOM_APN" CUSTOM_APN="tely360" APN_USER='tely360' APN_PASS='tely360'" --sakisswitches "--sudo --console" --devicename 'U20' --log --nat 'no' --httpserver
cd /

