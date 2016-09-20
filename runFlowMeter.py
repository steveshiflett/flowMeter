#!/usr/bin/env python
#
# This program reads the serial port which sends data from Adruino.
#
# The Adruino is configured to a 2" flow meter that converts analog
# data to digital.
import MySQLdb
import sys
temp = sys.stdout                 # store original stdout object for later
sys.stdout = open('/tmp/Flow.log.txt', 'w') # redirect all prints to this log file

conn = MySQLdb.connect(host= "localhost",
                  user="pi",
                  passwd="r00td0wn",
                  db="pi")
x = conn.cursor()

import serial
from time import strftime
# Serial port connection
try:
        ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
except:
        ser = serial.Serial('/dev/ttyACM1', 9600, timeout=1)

pulses = 0;
liters = 0;
piece = "Initialize";
DEVICE='Steve'
data = ' ';
minFlow = 0.001;  # The flow meter throws this out - and zero values for some reason.
while True:
# Read line received
	now=strftime("%Y-%m-%d %H:%M:%S")
	line = ser.readline().strip()
	if line:
		print(line)
        # Remove possible garbage lines
		if line.startswith(bytes('Temperature')):
			print "Found Temp"
			piece = line.split(b':')
			temperature = int(piece[1].strip())
			location = int(piece[2].strip())
			try:
					print "inserting..."
					x.execute("INSERT INTO Temp(temperature,location) VALUES (%s,%s)",(temperature,location))
					conn.commit()
			except MySQLdb.Error, e:
					try:
							print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
							if e.args[0]==2006:
								try:
									conn = MySQLdb.connect(host= "localhost",
									user="pi",
									passwd="r00td0wn",
									db="pi")
									x = conn.cursor()
									print( "Reconnected...")
									x.execute("INSERT INTO Temp(temperature,location) VALUES (%s,%s)",(temperature,location))
									conn.commit()
								except MySQLdb.Error, e:
									try:
										print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
									except IndexError:
										print "MySQL Error: %s" % str(e)
										conn.rollback()
					except IndexError:
						print "MySQL Error: %s" % str(e)			
					print( temperature,location,now )		
		if line.startswith(bytes('pulses')):
			piece = line.split(b':')
		if 2==len(piece):
			pulses = float(piece[1].strip())
            # print (pulses)
			liters = float(pulses)/5600
            # print (liters)
			data = {"Time":now,"data":{"liters":round(liters, 3)}}

        try:
                if liters > minFlow:
                        x.execute("INSERT INTO Flow(flow) VALUES (%s)",(round(liters, 3)))
                        conn.commit()
        except MySQLdb.Error, e:
                try:
                        print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
                        if e.args[0]==2006:  # Added this stuff because mysql server drops connection if it is idle for a long time
                                try:
                                        conn = MySQLdb.connect(host= "localhost",
                                                user="pi",
                                                passwd="r00td0wn",
                                                db="pi")
                                        x = conn.cursor()
                                        print( "Reconnected...")
                                        if liters > minFlow:
                                                x.execute("INSERT INTO Flow(flow) VALUES (%s)",(round(liters, 3)))
                                                conn.commit()
                                except MySQLdb.Error, e:  # Well, things are really hosed if we get here!
                                        try:
                                                print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
                                        except IndexError:
                                                print "MySQL Error: %s" % str(e)
                                                conn.rollback()
                except IndexError:
                        print "MySQL Error: %s" % str(e)

        # print(data)
        sys.stdout.flush()
conn.close()
sys.stdout.close()                # ordinary file object
sys.stdout = temp                 # restore print commands to interactive prompt

