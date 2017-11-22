# rest-dumper
This is a program the uses the F5-SDK Python module to dump config onto BIG-IP. 
It is slow and not refactored. It is not usefule to cofnig a BIG-IP but more to test the REST API and use later to see how to make basic objects.


There needs to be an include folder in directory where run from and place the following file in it:

$ ls -lrt
total 12
-rw-rw-r-- 1 tthomas tthomas  933 Nov 20 10:48 logger-irule.txt
-rw-rw-r-- 1 tthomas tthomas 1687 Nov 20 10:48 irule1.txt
-rw-rw-r-- 1 tthomas tthomas 1148 Nov 20 10:48 data_group.txt



$ ./rest-dumper.py -h
Usage: rest-dumper.py [options]

Options:
  -h, --help            show this help message and exit
  -d, --debug           Print out arg values given
  -u REMUSER, --user=REMUSER
                        Remote user name
  -p REMPASS, --pass=REMPASS
                        Remote user name
  -a ADDRESS, --address=ADDRESS
                        address of remote device
  -n NAMEPREFIX, --name=NAMEPREFIX
                        global name prefix for the opbject group being created
  -t TARGET, --target=TARGET
                        address that will be used in example if -e is used
  -v VSADDRESS, --vs=VSADDRESS
                        address that will be used for Virtual server
                        destination
  -r REMOVEAFTERSECONDS, --remove=REMOVEAFTERSECONDS
                        Take arg of second and will remove objects created
                        after sleeping for n seconds, if not present will not
                        remove
