 #!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class in Python 2.7 that executes a Thread for reading RFID tags.

"""

import threading
import signal
import RPi.GPIO as GPIO
from module.gpio import PinsGPIO
from time import sleep, gmtime, strftime
from module.MFRC522 import MFRC522
from module.pins import PinControl
import RPi.GPIO as GPIO
import MySQLdb
import time
import SocketioHandle
import json
import os
import cv2
import datetime

db = MySQLdb.connect("localhost", "root", "Hehe@123", "smart_parking")
cursor = db.cursor()
parkId = "p1"

continue_reading = True
cardSwifted = False
cardRfid = ""
plateNumber = ""
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(20,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(21,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
pwm1 = GPIO.PWM(18, 50)
pwm1.start(13)


def end_read(signal,frame):
    global continue_reading
    print ("Ctrl+C captured, ending read.")
    continue_reading = False
    GPIO.cleanup()

    signal.signal(signal.SIGINT, end_read)
         
def passBarrie(rfid,carplate,arrivalTime,money):
    global cardSwifted
    global cardRfid
    global plateNumber
    if carplate != '':
        print(time)
        SocketioHandle.sendCardMessage(json.dumps({'status':'1','message':'RFID was matched\nPlate Number: '+carplate, 'filename':rfid+'_lastest.jpg'}))
        cardSwifted = True
        cardRfid = rfid
        plateNumber = carplate
    else:
        SocketioHandle.sendCardMessage(json.dumps({'status':'1','message':'RFID was matched\nArrival time: '+arrivalTime+'\nPaymen: '+money,'filename':rfid+'_lastest.jpg'}))
        pwm1.ChangeDutyCycle(7.5)
        sql = "select * from park where parkId= '%s';" % (parkId)
        cursor.execute(sql)
        data = cursor.fetchall()
        numOfCar = data[0][7] -1
        sql = "update park set numOfCar = '%d' where parkId= '%s';" % (numOfCar, parkId)
        print("Update availableSlot %d" %(numOfCar))
        cursor.execute(sql)
        db.commit()
        os.system("curl -s -o /dev/null http://localhost:8080/2/action/snapshot")
        checkDelay = False
        while not (checkDelay and GPIO.input(20) and GPIO.input(21)):
            checkDelay=False
            if GPIO.input(20) & GPIO.input(21):
                checkDelay=True
                time.sleep(1)
        time.sleep(1)
        pwm1.ChangeDutyCycle(13)
        SocketioHandle.sendCardMessage(json.dumps({'status':'0','message':''}))
        img=cv2.imread('/home/pi/ProjectPython/TwoRC522_2/stream_save/lastsnap.jpg',1)
        filename = rfid+strftime("%Y-%m-%d%H:%M:%S", gmtime())+'.jpg'
        cv2.imwrite('/home/pi/smartparking/React/public/out/'+filename,img)
        sql = "insert into parkHistory(plateNumber,UID, fileName, createDate,status) value('%s','%s','%s',now(),1);" % (carplate, rfid, filename)
        cursor.execute(sql)
        db.commit()

class Nfc522(object):
    
    pc = PinControl()
    # GPIO.setup(24,GPIO.OUT)    # Code For Turn ON/OFF Buzzer
    MIFAREReader = None
    RST1 = 22 #GPIO
    RST2 = 27 #GPIO
    SPI_DEV0 = '/dev/spidev0.0'
    SPI_DEV1 = '/dev/spidev0.1'

    def get_nfc_rfid(self, autenticacao=True):

        print ("Welcome to the MFRC522 data read example")
        print ("Press Ctrl-C to stop.")

        MIFAREReader = MFRC522(self.RST2, self.SPI_DEV1)

        while continue_reading:

            # Scan for cards    
            (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

            # If a card is found
            # if status == MIFAREReader.MI_OK:
                # print "Card detected"     
            
            # Get the UID of the card
            (status,uid) = MIFAREReader.MFRC522_Anticoll()

            # If we have the UID, continue
            if status == MIFAREReader.MI_OK:

                # Print UID
                print ("Card read UID: ",str(uid[0]),",",str(uid[1]),",",str(uid[2]),",",str(uid[3]))
                

                # GPIO.output(24,GPIO.HIGH)   # Code For Turn ON/OFF Buzzer
                # sleep(0.1)
                # GPIO.output(24,GPIO.LOW)
                
                # This is the default key for authentication
                key = [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF]
                
                # Select the scanned tag
                MIFAREReader.MFRC522_SelectTag(uid)

                # Authenticate
                status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 8, key, uid)

                # Check if authenticated
                if status == MIFAREReader.MI_OK:
                    MIFAREReader.MFRC522_Read(8)
                    MIFAREReader.MFRC522_StopCrypto1()
                    try:
                        sql = "select * from carplate where UID='%s%s%s%s' and availableDate >= CURDATE();" % (str(uid[0]),str(uid[1]),str(uid[2]),str(uid[3]))
                        cursor.execute(sql)
                        data = cursor.fetchall()
                        sql = "select * from carplate where UID='%s%s%s%s';" % (str(uid[0]),str(uid[1]),str(uid[2]),str(uid[3]))
                        cursor.execute(sql)
                        data1 = cursor.fetchall()        
                        if len(data) > 0:
                            passBarrie(str(uid[0])+str(uid[1])+str(uid[2])+str(uid[3]),data[0][1],'',0)
                        else:
                            if len(data1)>0:
                                SocketioHandle.sendCardMessage(json.dumps({'status':'3','message':'RFID was expired'}))
                                db.commit()
                            else:
                                sql = "select * from card where UID='%s%s%s%s' and status=0;" % (str(uid[0]),str(uid[1]),str(uid[2]),str(uid[3]))
                                cursor.execute(sql)
                                data = cursor.fetchall()
                                if len(data)>0:
                                    sql = "update card set status = 1 where UID= '%s%s%s%s';" % (str(uid[0]),str(uid[1]),str(uid[2]),str(uid[3]))
                                    cursor.execute(sql)
                                    db.commit()
                                    sql = "select createDate, HOUR(TIMEDIFF(now(), createDate)) from parkHistory where UID='%s%s%s%s' and status =0 ORDER  BY createDate DESC LIMIT  1;" % (str(uid[0]),str(uid[1]),str(uid[2]),str(uid[3]))
                                    cursor.execute(sql)
                                    data = cursor.fetchall()
                                    if len(data)>0:
                                        passBarrie(str(uid[0])+str(uid[1])+str(uid[2])+str(uid[3]),'',data[0][0].strftime('%Y-%m-%d %H:%M:%S'),str((data[0][1]+1)*30000)+" VND")
                                    else:
                                        passBarrie(str(uid[0])+str(uid[1])+str(uid[2])+str(uid[3]),'','not found',0)
                                else:
                                    SocketioHandle.sendCardMessage(json.dumps({'status':'3','message':'RFID wasn\'t matched'}))
                                    db.commit()
                        # end if
                    except (MySQLdb.Error, MySQLdb.Warning) as e:
                        print(e)
                else:
                    print ("Authentication error")
                

class CardReader(threading.Thread):
    
    nfc = Nfc522()
    card_number = None
            
    def run(self):
        print (self.name,". Run... ") 
        self.read()
        
    def get_rfid_card_number(self):
        id = None
        try:
            while True:
                id = self.nfc.get_nfc_rfid()
                if id:
                    id = str(id).zfill(10)
                    if (len(id) >= 10):
                        self.card_number = id
                        print ("Read TAG Number: ",str(self.card_number))
                        return self.card_number
                    else:
                        print ("Error TAG Number: " ,str(self.card_number))
                        id = None
                        return None
                else:
                    return id
        except Exception as e:
            print (e)
            
    def read(self):
        try:
            self.get_rfid_card_number()
                # self.valida_cartao(self.card_number)
            return None
        except Exception as e:
            print (e)
            
    # def valida_cartao(self, numero):
    #     try:
    #         print "I make interesting operations here with the tag:" + str(numero)
    #     except Exception as e:
    #         print e


