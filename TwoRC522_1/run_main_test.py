#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class in Python 2.7 for testing two RFID readers with Raspberry Pi.

Use: 
$ cd TwoRC522RPi/
$ sudo python run_main_test.py 
Press Ctrl + z to finish.

"""

import sys
from module.card_reader import CardReader
import module.card_reader
import SocketioHandle
from threading import Thread
import time
import DetectNumber
import DetectPlate
import cv2
import os
import MySQLdb
import json
from time import sleep, gmtime, strftime

db = MySQLdb.connect("localhost", "root", "Hehe@123", "smart_parking")
cursor = db.cursor()
parkId = "p1"
detectedCheck = False
detectedNumber = ""
detectedRfid = ""
def detectCarPlate():
    global detectedCheck
    global detectedNumber
    global detectedRfid
    while True:
        if module.card_reader.GPIO.input(23)==0 and detectedCheck == False:
            os.system("curl -s -o /dev/null http://localhost:8080/1/action/snapshot")
            time.sleep(0.5)
            frame = cv2.imread("/home/pi/ProjectPython/TwoRC522_1/stream_save/lastsnap.jpg",1)
            crop = frame[150:400, 200:500]
            listOfPossiblePlates = DetectPlate.dectecPlatesInImage(crop)
            if len(listOfPossiblePlates) > 0:
                listOfPossiblePlates.sort(key=lambda possiblePlate: len(possiblePlate.strChars), reverse=True)
                number = DetectNumber.detectNumberFromPlate(listOfPossiblePlates[0])
                print(number.replace(".",""))
                sql = "select * from carplate where carNumPlate='%s' and availableDate >= CURDATE() and status = 1;" % (number.replace(".",""))
                cursor.execute(sql)
                db.commit()
                data = cursor.fetchall()
                if (len(data)>0):
                    rfid = data[0][3]
                    SocketioHandle.sendCarMessage(json.dumps({'status':'1','message':'Plate Number: '+number}))
                    detectedCheck = True
                    detectedNumber = number
                    detectedRfid = rfid
def monthTicketProcess():
    global detectedCheck
    global detectedNumber
    global detectedRfid
    while True:
        if module.card_reader.GPIO.input(23)!=0:
            detectedCheck = False
            module.card_reader.cardSwifted = False
        if detectedCheck == True and module.card_reader.cardSwifted==True:
            if detectedNumber.replace(".","").replace(" ","") == module.card_reader.plateNumber and detectedRfid == module.card_reader.cardRfid:
                module.card_reader.pwm1.ChangeDutyCycle(6.5)
                sql = "select * from park where parkId= '%s';" % (module.card_reader.parkId)
                cursor.execute(sql)
                data = cursor.fetchall()
                numOfCar = data[0][7] +1
                sql = "update park set numOfCar = '%d' where parkId= '%s';" % (numOfCar, module.card_reader.parkId)
                print("Update number car %d" %(numOfCar))
                cursor.execute(sql)
                db.commit()
                checkDelay = False
                while not (checkDelay and module.card_reader.GPIO.input(23) and module.card_reader.GPIO.input(24)):
                    checkDelay=False
                    if module.card_reader.GPIO.input(23) & module.card_reader.GPIO.input(24):
                        checkDelay=True
                        time.sleep(1)
                time.sleep(1)
                module.card_reader.pwm1.ChangeDutyCycle(12)
                SocketioHandle.sendCarMessage(json.dumps({'status':'0','message':''}))
                SocketioHandle.sendCardMessage(json.dumps({'status':'0','message':''}))
                img=cv2.imread('/home/pi/ProjectPython/TwoRC522_1/stream_save/lastsnap.jpg',1)
                filename = detectedRfid+'_lastest.jpg'
                cv2.imwrite('/home/pi/smartparking/React/public/in/'+filename,img)
                filename = detectedRfid+strftime("%Y-%m-%d%H:%M:%S", gmtime())+'.jpg'
                cv2.imwrite('/home/pi/smartparking/React/public/in/'+filename,img)
                sql = "insert into parkHistory(plateNumber,UID, fileName, createDate,status) value('%s','%s','%s',now(),0);" % (module.card_reader.plateNumber, module.card_reader.cardRfid, filename)
                cursor.execute(sql)
                db.commit()
                detectedCheck = False;
                module.card_reader.cardSwifted = False
            else:
                module.card_reader.cardSwifted = False

def main(self):
    card_reader = CardReader()
    detectPlate= Thread(target=detectCarPlate,args=())
    monthTicketThread = Thread(target=monthTicketProcess,args=())
    try:
        card_reader.start()
        detectPlate.start()
        monthTicketThread.start()
    except KeyboardInterrupt:
        print ("trl+C received! Sending kill to " , reader_card.getName())
        if reader_card.isAlive():
            reader_card._stopevent.set()
    SocketioHandle.run()
            
if __name__ == '__main__':
    main(sys.argv)