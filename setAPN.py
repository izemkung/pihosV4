import os

config_path = '/home/pi/usb/apn_configure.cfg'
try:
    os.system('sudo mkdir /home/pi/usb/')
    os.system('sudo mount /dev/sda1 /home/pi/usb/')
    print("USB found!!")
except:
    print("Not found")

file_exists = os.path.exists(config_path)
apn_string_list = ''

if(file_exists):
    print("Config found!!")
    usb_apn_file = open(config_path)
    apn_string_list = usb_apn_file.readlines()
    usb_apn_file.close()
    for idx in range(0, len(apn_string_list)):
        line = apn_string_list[idx]
        if 'apn=' in line:
            first_idx = line.find('=') + 1
            usbAPN = line[first_idx:].strip('\n')
            print('USB APN : '+ usbAPN)
else:
    print("Config not found!!")
    exit()

my_file_path =  "/usr/src/qmi_reconnect.sh"
my_file = open(my_file_path)
string_list = my_file.readlines()
my_file.close()
apn = usbAPN
for idx in range(0, len(string_list)):
    line = string_list[idx]
    if 'quectel-CM' in line:
        first_idx = line.find('-s') + 3
        currentID = line[first_idx:].strip('\n')
        print('current APN : '+ currentID)
        if( currentID != apn ):
            print("Update APN "+currentID+" > "+ apn)
            string_list[idx] = '\t\tsudo ./quectel-CM -s ' + apn + '\n'
        #sudo ./quectel-CM -s tely360
        #    print(string_list[idx])
            my_file = open(my_file_path, "w")
            new_file_contents = "".join(string_list)
            my_file.write(new_file_contents)
            my_file.close()
            os.popen("sudo systemctl restart qmi_reconnect.service")
        #    print("Reboot hostapd Service")
            #reconnect camera
        else:
            print("Current APN = new APN : " + apn)