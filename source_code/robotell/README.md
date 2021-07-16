# Akostar CAN example for robotell interface

  This example drives the Akostar IOCOMx device from the can bus.

  Simple Usage:

      ./robotell.pl -p /dev/TTYUSB0 --ord 0 --mask 255 --value 255

          to switch on all swithes on the first unit (1-2)

      ./robotell.pl -p /dev/TTYUSB0 --ord 1 --mask 255 --value 255


  Usage:

    Type ./robotell.py -h for a more elaborate description of the


 Just for completeness the python USB drivers are included here in the python_can
 subdirectory.


## The Original message

### INSTALLING ROBOTELL PYTHON MODULES

  The official python-can repositiry does not contain support for the robotell CAN.

But it can be installed from the github repo from:

    https://github.com/hardbyte/python-can

    python setup.py install    (may need sudo if global install needed)

    [Remove the pip version before installing from source.]

PG

