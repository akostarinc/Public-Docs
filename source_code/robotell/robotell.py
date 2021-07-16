#!/usr/bin/env python3
#
# Supporting documentation at:
#
# https://python-can.readthedocs.io/en/develop/interfaces/robotell.html
#
#  'pip install python-can' does not give the robotell code, install it from:
#
#       https://github.com/hardbyte/python-can
#
# History:
#       Fri 16.Jul.2021
#

from __future__ import absolute_import
from __future__ import print_function

import array, time, threading, getopt, sys
import can, can.interfaces

#print(dir(can.interfaces))
#print (can.interfaces.BACKENDS)

# ------------------------------------------------------------------------
# Basic comm definitions to can  (replicated from can.h Fri 16.Jul.2021)

MSG_SWITCHES   = 0x19EE5501  #// Intro IOCOMx msg to funnel to RF
MSG_TID        = 0x19EE5502  #// Intra IOCOMx msg / presence check
MSG_MASKS      = 0x19EE5503  #// Intra IOCOMx msg mask
MSG_RELAYS     = 0x19EE5504  #// Control local relays
MSG_BRIDGE     = 0x19EE5505  #// Control remote relays (note: timeout)
MSG_INPUTS     = 0x19EE5506  #// The status of the inputs
MSG_OUTPUTS    = 0x19EE5507  #// The status of the outputs
MSG_MASKAUX    = 0x19EE5508  #// IOCOM auxiliary mask
MSG_AUX        = 0x19EE5509  #// IOCOM auxiliary command
MSG_RESERVED   = 0x19EE550a  #// IOCOM reserved for future use

msgid    =  MSG_AUX
msgmask  =  MSG_MASKAUX

serport     = '/dev/ttyUSB0'
bitrate     = 250000
ifacename   = 'robotell'

maskx   = 0
valuex  = 0
ordx    = 0

pgdebug = 0
verbose = 0
listen  = 0
bridge  = 0
count = 0

old_rx = None   #can.Message()

# ------------------------------------------------------------------------
# Convert in str NNN and  0xNNN str to number

def hexint(nnn):
    if nnn[:2].lower() == "0x":
        return int(nnn[2:], 16)
    else:
        return int(nnn)

def pdevices():
    print ("Valid CAN interfaces:")
    for aa in can.interfaces.VALID_INTERFACES:
        print(aa, end = " ")
    print()

def _(aa):
    return aa

# ------------------------------------------------------------------------

def receive(bus, stop_event):
    """The loop for receiving."""

    if verbose:
        print("Start receiving messages")

    global old_rx, count

    while not stop_event.is_set():
        rx_msg = bus.recv(1)
        if rx_msg is not None:
            if rx_msg.data != old_rx.data:
                print("rx:{0} {1}\n".format(count, rx_msg))
                count = 0
                old_rx = rx_msg
            else:
                #print("filtered", rx_msg.data)
                count += 1
    if verbose:
        print("Stopped receiving messages")

# ------------------------------------------------------------------------

def sendit(bus, message):

    if message is not None:
        print("tx: {}".format(message))

    cnt = 0
    while(True):
        bus.send(message, timeout=0.2)
        if not bridge:
            break;
        time.sleep(0.300)

        if bridge and not cnt:
            print("Sustaining BRIDGE transmission, CTRL-C to exit", end = " ")
            sys.stdout.flush()
        cnt+= 1

# ------------------------------------------------------------------------

def send_vals(bus, strx):

    global CANPACK, msgid

    # Passed as one argument, split it
    if len(strx) == 1:
        strx = str.split(strx[0])

    if pgdebug > 4:
        print("processing: ", strx)

    arr2 = []
    for aa in strx:
        arr2.append(hexint(aa))

    xlen = len(arr2)

    if verbose:
        print("Sending: ", arr2)
        #print("4", arr2[:4], arr2[4:8])
        #print("8", arr2[8:12], arr2[12:16])

    # Only change if original op code, else accept custom
    if bridge and msgid == MSG_AUX:
        msgid = MSG_BRIDGE

    if xlen == 16:
        # Send mask
        message = can.Message(arbitration_id=msgmask, is_extended_id=True,
                            check=True, data=arr2[:4] )
        sendit(bus, message)
        # Send value
        message2 = can.Message(arbitration_id=msgid, is_extended_id=True,
                            check=True, data=arr2[4:8] )
        sendit(bus, message2)

         # Send mask
        message = can.Message(arbitration_id=msgmask, is_extended_id=True,
                            check=True, data=arr2[8:12] )
        sendit(bus, message)
        # Send value
        message2 = can.Message(arbitration_id=msgid, is_extended_id=True,
                            check=True, data=arr2[12:16] )
        sendit(bus, message2)

    elif xlen == 8:
        # Send mask
        message = can.Message(arbitration_id=msgmask, is_extended_id=True,
                            check=True, data=arr2[:4] )
        sendit(bus, message)
        # Send value
        message2 = can.Message(arbitration_id=msgid, is_extended_id=True,
                            check=True, data=arr2[4:] )
        sendit(bus, message2)
    else:
        print()
        print("Please give CAN IOCOMX arguments in packs of eight in the forms of:")
        print()
        print("mask1 mask2 mask3 mask4 value1 value2 value3 value4")
        print("Where 'mask' is the bit mask of the effected switches, and")
        print("value is the on / off value per bit")
        print()
        print("Alternatively, send mask with a --mask option and value")
        print("with a --value option")
        return

def errexit(err_str, exitval = 0):
    print(err_str)
    sys.exit(exitval)

# ------------------------------------------------------------------------
# Many other interfaces are supported as well (see below)

def main(args):

   # Create a bus instance
    bus = None
    try:
        bus = can.Bus(interface=ifacename,
                  channel=serport,
                  receive_own_messages=True)
    except:
        print("Cannot connect to interface:", serport)
        if verbose:
            print(sys.exc_info())
        sys.exit(1)

    if not bus:
        print("No bus to connect to:", serport)
        sys.exit(2)

    serno = bus.get_serial_number(0)
    if verbose:
        print ("USB CAN Serial number:", serno)

    bus.set_bitrate(bitrate)

    # See if any mask specified and generate args
    if maskx:
        if verbose:
            print("maskx =", maskx, "valuex =", valuex, "ordx =", ordx)

        # Error check arguments
        if ordx < 0:
            errexit("Ordinal must be between 0-7")
        if ordx > 8:
            errexit("Ordinal must be less than 8")
        if maskx > 255 or maskx < 0:
            errexit("Mask must be less than 256 or greater than zero")
        if valuex > 255:
            errexit("Value must be less than 256")

        for aa in range(16):
            args.append("0")

        args[ordx] = str(maskx); args[ordx + 4] = str(valuex)

    try:
        send_vals(bus, args)
    except:
        if pgdebug > 3:
            print("Could not send", sys.exc_info())
            raise

        print("Invalid value, all arguments must be decimal numbers ... ")
        print("  ... or hex numbers with the 0x prefix. For example: '0x1a' (which is '26')")
        return

    if listen:
        # Thread for sending and receiving messages
        stop_event = threading.Event()
        try:
            t_receive = threading.Thread(target=receive, args=(bus, stop_event))
            t_receive.start()

        except KeyboardInterrupt:
            print()
            print("Received keyboard interrupt, aborting")
        except:
            print("Interrupt")
            pass  # exit normally


        # iterate over received messages
        #for msg in bus:
        #    print("{X}: {}".format(msg.arbitration_id, msg.data))

        # or use an asynchronous notifier
        #notifier = can.Notifier(bus, [can.Logger("recorded.log"), can.Printer()])

        #stop_event.set()
        #time.sleep(0.5)

def helpx():
    print("Akostar CAN test utility. Partial (C) Akostar Inc; Released as Open Source.")
    print("Use: robotell.py [options] data1 .. dataN")
    print("   Where options can be:")
    print("     -V          --version    print version")
    print("     -h          --help       print help")
    print("     -c          --devices    print supported devices")
    print("     -t          --timing     show timing")
    print("     -i          --interface  interface board (def: robotell)")
    print("     -l          --listen     listen")
    print("     -g          --bridge     bridge")
    print("     -v          --verbose    verbose")
    print("     -p  port    --port       serial port (def: /dev/ttyUSB0)")
    print("     -b  bitrate --bitrate    bit rate (def: 250000)")
    print("     -i  message --message    message id (def=0x19EE5504 )")
    print("     -m  mask    --mask       effective bit mask")
    print("     -u  value   --value      value to send to device")
    print("     -o  ord     --ord        ordinal to send to")
    print("     -d  level   --debug      debug level")
    print(" Arguments for short options also needed for the long options.")
    sys.exit(1)

longopt = ["help", "message=", "version",  "devices", "timing", "bitrate=",
                "interface=", "listen", "bridge", "verbose", "port=",
                    "debug=", "mask=", "value=", "ord=" ]

# ------------------------------------------------------------------------
# Start of program:

if __name__ == '__main__':

    opts = []; args = []

    try:
        opts, args = getopt.getopt(sys.argv[1:], "bd:p:h?fvxctVoli:go:", longopt)
    except getopt.GetoptError as err:
        print(_("Invalid option(s) on command line:"), err)
        sys.exit(1)

    if not len(args) and not len(opts):
        print("No arguments passed, use -h or --help option for usage info.")
        exit(0)

    for aa in opts:
        # in line verbose
        if pgdebug:
            print("parsing:", aa)

        if aa[0] == "-d" or aa[0] == "--debug":
            try:
                pgdebug = int(aa[1])
            except:
                print("Warn: invalid debug level:", "'" + aa[1] + "'")
                pgdebug = 0
            if verbose:
                print( sys.argv[0], "running at debug level",  pgdebug)

        if aa[0] == "-?": helpx()
        if aa[0] == "-h" or aa[0] == "--help": helpx()
        if aa[0] == "-V" or aa[0] == "--version": print("robotell interface version", 1.0);  sys.exit(0)
        if aa[0] == "-c" or aa[0] == "--devices": pdevices(); sys.exit(0);
        if aa[0] == "-p" or aa[0] == "--port": serport = aa[1]
        if aa[0] == "-b" or aa[0] == "--bitrate": bitrate = int(aa[1])
        if aa[0] == "-i" or aa[0] == "--interface": ifacename = aa[1]
        if aa[0] == "-i" or aa[0] == "--message": msgid = aa[1]
        if aa[0] == "-l" or aa[0] == "--listen": listen = True
        if aa[0] == "-t" or aa[0] == "--timing": show_timing = True
        if aa[0] == "-o" or aa[0] == "--stdout": use_stdout = True
        if aa[0] == "-v" or aa[0] == "--verbose": verbose = True
        if aa[0] == "-g" or aa[0] == "--bridge": bridge = True
        if aa[0] == "-m" or aa[0] == "--mask":  maskx = hexint(aa[1])
        if aa[0] == "-u" or aa[0] == "--value": valuex = hexint(aa[1])
        if aa[0] == "-o" or aa[0] == "--ord": ordx = hexint(aa[1])

    if pgdebug > 1:
        print ("opts", opts, "args", args)
        print("Comm =", serport)

    main(args)

# eof
