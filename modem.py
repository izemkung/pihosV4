from __future__ import print_function
import sys

from gsmmodem.modem import GsmModem
from gsmmodem.exceptions import TimeoutException, PinRequiredError, IncorrectPinError

from netifaces import interfaces, ifaddresses, AF_INET

def parseArgs():
    """ Argument parser for Python 2.7 and above """
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Identify and debug attached GSM modem')    
    parser.add_argument('port', metavar='PORT', help='port to which the GSM modem is connected; a number or a device name.')
    parser.add_argument('-b', '--baud', metavar='BAUDRATE', default=115200, help='set baud rate')
    parser.add_argument('-p', '--pin', metavar='PIN', default=None, help='SIM card PIN')
    parser.add_argument('-d', '--debug',  action='store_true', help='dump modem debug information (for python-gsmmodem development)')    
    return parser.parse_args()

def parseArgsPy26():
    """ Argument parser for Python 2.6 """
    from gsmtermlib.posoptparse import PosOptionParser, Option    
    parser = PosOptionParser(description='Identify and debug attached GSM modem')        
    parser.add_positional_argument(Option('--port', metavar='PORT', help='port to which the GSM modem is connected; a number or a device name.'))
    parser.add_option('-b', '--baud', metavar='BAUDRATE', default=115200, help='set baud rate')
    parser.add_option('-p', '--pin', metavar='PIN', default=None, help='SIM card PIN')
    parser.add_option('-d', '--debug',  action='store_true', help='dump modem debug information (for python-gsmmodem development)')
    options, args = parser.parse_args()
    if len(args) != 1:    
        parser.error('Incorrect number of arguments - please specify a PORT to connect to, e.g. {0} /dev/ttyUSB0'.format(sys.argv[0]))
    else:
        options.port = args[0]
        return options


def main():
    args = parseArgsPy26() if sys.version_info[0] == 2 and sys.version_info[1] < 7 else parseArgs()
    print ('args:',args)
    modem = GsmModem(args.port, args.baud)    
    
    print('Connecting to GSM modem on {0}...'.format(args.port))
    try:
        modem.connect(args.pin)
    except PinRequiredError:
        sys.stderr.write('Error: SIM card PIN required. Please specify a PIN with the -p argument.\n')
        sys.exit(1)
    except IncorrectPinError:
        sys.stderr.write('Error: Incorrect SIM card PIN entered.\n')
        sys.exit(1)

  
    
    if args.debug:
        # Print debug info
        print('\n== MODEM DEBUG INFORMATION ==\n')
        #print('ATI', modem.write('ATI', parseError=False))
        print('AT+CGMI:', modem.write('AT+CGMI', parseError=False))
        print('AT+CGMM:', modem.write('AT+CGMM', parseError=False))
        print('AT+CGMR:', modem.write('AT+CGMR', parseError=False))
        print('AT+CFUN=?:', modem.write('AT+CFUN=?', parseError=False))
        print('AT+WIND=?:', modem.write('AT+WIND=?', parseError=False))
        print('AT+WIND?:', modem.write('AT+WIND?', parseError=False))
        print('AT+CPMS=?:', modem.write('AT+CPMS=?', parseError=False))
        print('AT+CNMI=?:', modem.write('AT+CNMI=?', parseError=False))
        print('AT+CVHU=?:', modem.write('AT+CVHU=?', parseError=False))
        print('AT+CSMP?:', modem.write('AT+CSMP?', parseError=False))
        print('AT+GCAP:', modem.write('AT+GCAP', parseError=False))
        print('AT+CPIN?', modem.write('AT+CPIN?', parseError=False))
        print('AT+CLAC:', modem.write('AT+CLAC', parseError=False))
        print()
    else:
        # Print basic info
        print('\n== MODEM INFORMATION ==\n')

        


        print('Manufacturer:', modem.manufacturer)
        print('Model:', modem.model)
        print('Revision:', modem.revision if modem.revision != None else 'N/A')
        print('\nIMEI:', modem.imei if modem.imei != None else 'N/A')
        print('IMSI:', modem.imsi if modem.imsi != None else 'N/A')
        
         
        print('\nNetwork:', modem.networkName)
        print('Signal strength:', modem.signalStrength)
        
        print('\n\nATI;', modem.write('ATI', parseError=False))
        print('AT+CGSN:', modem.write('AT+CGSN', parseError=False))
        print('AT+CIMI:', modem.write('AT+CIMI', parseError=False))
        print('AT+QCCID:', modem.write('AT+QCCID', parseError=False))
        print('AT+QSPN:', modem.write('AT+QSPN', parseError=False))
        print('AT+CSQ:', modem.write('AT+CSQ', parseError=False))
        print('AT+QNWINFO:', modem.write('AT+QNWINFO', parseError=False))
        print('AT+CSTT=?:', modem.write('AT+CSTT=?', parseError=False))
        print('AT+CIFSR:', modem.write('AT+CIFSR', parseError=False))


        
        addresses = [i['addr'] for i in ifaddresses('wwan0').setdefault(AF_INET, [{'addr':'No IP addr'}] )]
        print( '%s: %s' % ('wwan0', ', '.join(addresses)))

        print()

if __name__ == '__main__':
    main()