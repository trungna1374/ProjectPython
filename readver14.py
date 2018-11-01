import serial
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb
import time
import datetime
import re
import os
import logging
import subprocess
from subprocess import Popen, PIPE
import smbus
import time


I2C_ADDR  = 0x27 #I2C address
LCD_WIDTH = 16   #Character limit

LCD_CHR = 1 # Sent char
LCD_CMD = 0 # Sent command

LCD_LINE_1 = 0x80 # RAM address line 1
LCD_LINE_2 = 0xC0 # RAM address line 2


LCD_BACKLIGHT  = 0x08  # On
#LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# delay
E_PULSE = 0.0005
E_DELAY = 0.0005

bus = smbus.SMBus(1)

def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) 
  lcd_byte(0x32,LCD_CMD) 
  lcd_byte(0x06,LCD_CMD) 
  lcd_byte(0x0C,LCD_CMD)
  lcd_byte(0x28,LCD_CMD) 
  lcd_byte(0x01,LCD_CMD) 
  time.sleep(E_DELAY)

# Sent 1 byte to LCD
def lcd_byte(bits, mode):
	bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
	bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT
	bus.write_byte(I2C_ADDR, bits_high)
	lcd_toggle_enable(bits_high)

	bus.write_byte(I2C_ADDR, bits_low)
	lcd_toggle_enable(bits_low)

# Sent data
def lcd_toggle_enable(bits):
	bus.write_byte(I2C_ADDR, (bits | ENABLE))
	time.sleep(E_PULSE)
	bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
	time.sleep(E_DELAY)

# Sent data to LCD
def lcd_string(message,line):
	message = message.ljust(LCD_WIDTH," ")
	lcd_byte(line, LCD_CMD)
	for i in range(LCD_WIDTH):
		lcd_byte(ord(message[i]),LCD_CHR)

port = serial.Serial("/dev/ttyUSB0",baudrate=9600,timeout=0.2)
db= MySQLdb.connect("localhost", "root", "admin123", "iot")
cursor= db.cursor()
hostnm = 'RS1'
updateFlg = False
hostFlg = True
callFlg = True
smsFlgDHT11 = True
smsFlgMQ135 = True
smsFlgMC52 = True
print("Raspberry's receiving : ")
 
try:
    lcd_init()
    while True:
        elanip = ""
        wlanip = ""
        #Get Ethernet IP address
        elan = subprocess.Popen(["ifconfig","eth0"], stdout=PIPE)
        out, err = elan.communicate()
        for line in out.split('\n'):
            line = line.lstrip()
            if line.startswith('inet addr:'):
                elanip = line.split()[1][5:]
        #Get Wifi IP address
        wlan = subprocess.Popen(["ifconfig","wlan0"], stdout=PIPE)
        out, err = wlan.communicate()
        for line in out.split('\n'):
            line = line.lstrip()
            if line.startswith('inet addr:'):
                wlanip = line.split()[1][5:]
        #Display on LCD
        lcd_string("WX-Net Host "+hostnm,LCD_LINE_1)
        #If LAN cable plug in only show Ethernet IP address
        if elanip != "":
          lcd_string(elanip,LCD_LINE_2)
        elif wlanip != "":
          lcd_string(wlanip,LCD_LINE_2)
        else:
          lcd_string("Disconnect",LCD_LINE_2)
        #Read coming message 
        rcv = port.readline()
        data = rcv.rstrip() # cut "\r\n" at last of string
        if data != "":
            print(data) # print string
            if "ACKNO" in data:
                #Extract device ID and device type from ACKNO
                dvid = data[:(data.find("ACKNO"))]
                typedv = data[(data.find("TYP:")+4):]
                try:
                    #Check whether it connected before or not
                    sql = "SELECT loca_id FROM home where device_id = '%s'" % (dvid)
                    cursor.execute(sql)
                    data = cursor.fetchall()
                    row = data[0]
                    #If location index equal to 0 delete it in home table
                    if row[0] == 0:
                        sql = "DELETE FROM home where device_id = '%s'" % (dvid)
                        cursor.execute(sql)
                        db.commit()
                        #Throw Exception
                        raise IndexError
                    #Sent ACKYES
                    sentstr = dvid+"ACKYESHS:"+hostnm+"\n"
                    print(sentstr)
                    port.write(str(sentstr))
                    port.flush()
                except IndexError:
                    #Insert and update timestamp ack_list table
                    matchObj = re.match("DV[0-9]+$",dvid,re.I)
                    if (matchObj and (typedv == "DHT11" or typedv == "MC52" or typedv == "MQ135")):
                        ts = time.time()
                        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                        sql = "INSERT INTO ack_list (device_id, type) VALUES('%s', '%s') ON DUPLICATE KEY UPDATE type = '%s', timestamp = '%s'" % (dvid,typedv,typedv,st)
                        try:
                            cursor.execute(sql)
                            db.commit()
                        except Exception,e:
                                print(e)
                except Exception,e:
                    print(e)
                    continue
            if "TMP" in data:
                hs = data[0:data.find("TMP")]
                #If data is not belong to this host
                if hs != hostnm:
                    hostFLg = False
                else:
                    #Extract temperature data
                    dvid = data[(data.find("TMP")+3):data.find("DT:")]
                    typedv="DHT11"
                    temp = data[(data.find("DT:")+3):]
                    hostFLg = True
            if "HUM" in data:
                #Extract humidity data
                humi = data[(data.find("DT:")+3):]                
                updateFlg = True
            if "OPN" in data:
                hs = data[0:data.find("OPN")]
                #If data is not belong to this host
                if hs != hostnm:
                    hostFLg = False
                else:
                    #Extract open state data
                    dvid = data[(data.find("OPN")+3):data.find("DT:")]
                    typedv = "MC52"
                    dopen = data[(data.find("DT:")+3):]
                    updateFlg = True
                    hostFLg = True
            if "CO2" in data:
                hs = data[0:data.find("CO2")]
                #If data is not belong to this host
                if hs != hostnm:
                    hostFLg = False
                    continue
                else:
                    #Extract co2 data
                    dvid = data[(data.find("CO2")+3):data.find("DT:")]
                    typedv = "MQ135"
                    co2 = data[(data.find("DT:")+3):]
                    hostFLg = True
            if "COO" in data:
                #Extract co data
                co = data[(data.find("DT:")+3):] 
            if "ETH" in data:
                #Extract ethanol data
                ethanol = data[(data.find("DT:")+3):] 
            if "TOL" in data:
                #Extract toluene data
                toluene = data[(data.find("DT:")+3):] 
            if "ACE" in data:
                #Extract acetone data
                acetone = data[(data.find("DT:")+3):] 
            if "ANA" in data:
                #Extract analog data
                analog = data[(data.find("DT:")+3):]
                updateFlg = True
            #If it is time to update and message is belong to this device
            if updateFlg and hostFlg:
                try:
                    #Get data to check whether it still connected or in warning state
                    sql = "SELECT loca_id,warn,cmpsign1,warntemp,cmpsign2,warnhumi FROM home where device_id = '%s'" % (dvid)
                    cursor.execute(sql)
                    query = cursor.fetchall()
                    row = query[0]
                    locaid = row[0]
                    warn = row[1]
                    cmpsign1 = row[2]
                    warntemp = row[3]
                    cmpsign2 = row[4]
                    warnhumi = row[5]
                except Exception,e:
                    print(e)
                    continue
                # If location index equal to 0, it mean host want to disconnect
                if(locaid ==  0):
                    #Sent ACKNO command for disconecting
                    print("SENT ACKNO")
                    port.write(dvid+"ACKNO")
                    port.flush()
                    updateFlg = False
                    print(dvid+"ACKNO")
                    continue
                #For timestamp
                ts = time.time()
                st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                if "DHT11" in typedv:
                    sms = ''
                    #Check whether data received is violate the thresehold
                    if warn == 1:
                        if cmpsign1 == 1 and float(temp) > warntemp:
                                sms = "Device "+dvid+" measure the temperature right now is "+temp+" hotter than your thresehold"
                        if cmpsign1 == 2 and float(temp) == warntemp:
                                sms = "Device "+dvid+" measure the temperature right now is "+temp+" equal your thresehold"
                        if cmpsign1 == 3 and float(temp) < warntemp:
                                sms = "Device "+dvid+" measure the temperature right now is "+str(temp)+" colder than your thresehold"
                        if cmpsign2 == 1 and float(humi) > warnhumi:
                                if sms != '':
                                    sms += ", and also the humidity right now is "+str(humi)+" higher than your thresehold"
                                else:
                                    sms = "Device "+dvid+" measure the humidity right now is "+str(humi)+" higher than your thresehold"
                        if cmpsign2 == 2 and float(humi) == warnhumi:
                                if sms != '':
                                    sms += ", and also the humidity right now is "+str(humi)+" equal your thresehold"
                                else:
                                    sms = "Device "+dvid+" measure the humidity right now is "+str(humi)+" equal your thresehold"
                        if cmpsign2 == 3 and float(humi) < warnhumi:
                                if sms != '':
                                    sms += ", and also the humidity right now is "+humi+" lower than your thresehold"
                                else:
                                    sms = "Device "+dvid+" measure the humidity right now is "+humi+" lower than your thresehold"
                    #smsFlgDHT11 is to reduce duplicate warining message
                    if sms == '':
                        smsFlgDHT11 = True
                    if warn == 1 and sms != '' and smsFlgDHT11:
                        subprocess.call(["python","smssos.py",sms])
                        smsFlgDHT11 = False
                    #Update home table
                    sql = "INSERT INTO home (device_id, type, temp, humi, warn) VALUES ('%s', '%s', %s, %s, '%s') ON DUPLICATE KEY UPDATE temp = %s, humi = %s, timestamp = '%s'" % (dvid,typedv,temp,humi,0,temp,humi,str(st))
                    #Insert in dht11 table
                    sql2 = "INSERT INTO dht11 (device_id, temp, humi) VALUES ('%s', '%s', %s)" % (dvid,temp,humi)
                elif "MC52" in typedv:
                    #Check whether data received is violate the thresehold
                    if dopen == '0':
                        callFlg = True
                        smsFLgMC52 = True
                    #callFlg and smsFlgMC52 is to reduce duplicate warining message
                    if warn == 1 and dopen == '1' and callFlg and smsFlgMC52:
                       subprocess.call(["python","callsos.py"])
                       sms = "Device "+dvid+" detected door is open right now"
                       subprocess.call(["python","smssos.py",sms])
                       callFlg = False
                       smsFlgMC52 = False
                    #Update home table
                    sql = "INSERT INTO home (device_id, type, open, warn) VALUES ('%s', '%s', %s, %s) ON DUPLICATE KEY UPDATE open = %s, timestamp = '%s'" % (dvid,typedv,dopen,0,dopen,str(st))
                    #Insert in mc52 table
                    sql2 = "INSERT INTO mc52 (device_id, open) VALUES ('%s', %s)" % (dvid,dopen)
                elif "MQ135" in typedv:
                    #Check whether data received is violate the thresehold
                    if analog < 200:
                        smsFlgMQ135 = True
                     #smsFlgMQ135 is to reduce duplicate warining message
                    if warn == 1 and int(analog) > 200:
                        sms = "Device "+dvid+" detected a problem with your air quality right now"
                        subprocess.call(["python","smssos.py",sms])
                        smsFlgMQ135 = False
                    #Update home table
                    sql = "INSERT INTO home (device_id, type, co2, co, ethanol, toluene, acetone, warn) VALUES ('%s', '%s', %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE co2 = %s, co = %s, ethanol = %s, toluene = %s, acetone = %s, timestamp = '%s'" % (dvid,typedv,co2,co,ethanol,toluene,acetone,0,co2,co,ethanol,toluene,acetone,str(st))         
                    #Insert in mc52 table
                    sql2 = "INSERT INTO mq135 (device_id, co2, co, ethanol, toluene, acetone) VALUES ('%s', %s, %s, %s, %s, %s)" % (dvid,co2,co,ethanol,toluene,acetone)
                matchObj = re.match("DV[0-9]+$",dvid,re.I)
                if(matchObj):
                    try:
                        #Query SQL
                        cursor.execute(sql)
                        cursor.execute(sql2)
                        db.commit()
                        upstr = "UPDATED ON %s" % (str(st))
                        print upstr
                        updateFlg = False
                    except MySQLdb.Error, e:
                        print sql+"\n";
                        print sql2+"\n";
                        print("Error with MySQL")
                        updateFlg = False
                    except Exception,e:
                        print sql;
                        print(e)
                        updateFlg = False
                               
except KeyboardInterrupt:
        port.close()
        db.close()

