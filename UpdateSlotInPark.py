import serial
import MySQLdb
import sys

#port = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=0.2)
port = serial.Serial("/dev/ttyUSB0",baudrate=115200)
db = MySQLdb.connect("localhost", "root", "Hehe@123", "smart_parking")
cursor = db.cursor()
parkId = "p1"
_station=1

MAX_MESSAGE = 50
MAX_COMMANDS = 10
SOH=1
STX=2
ETX=3
EOT=4
_recPhase = 0
_recPos = 0
_recLen = 0
_recCommand = 0
_recCS = 0
_recCalcCS = 0
_header = [0,0,0,0,0,0]
_data = [0,0,0,0,0,0,0,0,0,0]
_save = [48,48,48,48,48,48]

numberOfSlot = 0
numberOfAvailableSlot = 0
numberOfIncome = 0

def init():
    global numberOfSlot
    global numberOfAvailableSlot
    global numberOfIncome
    try:
        sql = "select * from park where parkId= '%s'" % (parkId)
        cursor.execute(sql)
        data = cursor.fetchall()
        if len(data)>0:
            numberOfSlot = data[0][5]
            numberOfAvailableSlot = data[0][6]
            numberOfIncome = data[0][7]
            print ("Init Success")
        # end if
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    return

def readFromRS485():
    rcv = port.readline()
    print(rcv)
    return

def reset():
    global _recPhase
    global _recPos
    global _recLen
    global _recCommand
    global _recCS
    global _recCalcCS
    _recPhase = 0
    _recPos = 0
    _recLen = 0
    _recCommand = 0
    _recCS = 0
    _recCalcCS = 0

def updateAvailableSlotToDB():
    global _recPhase
    global _recPos
    global _recLen
    global _recCommand
    global _recCS
    global _recCalcCS
    global numberOfSlot
    global numberOfAvailableSlot
    global numberOfIncome
    init()
    try:
        _inSeat=0
        print("start")
        while True:
            inch = int.from_bytes(port.read(),byteorder='big')
            if _recPhase==0:
                for i in range(5):
                    _header[i]=_header[i+1]
                _header[5] = inch
                if (_header[0] == SOH) & (_header[5] == STX) & (_header[1] != _header[2]):
                    _recCalcCS = 0
                    _recStation = _header[1]
                    _recSender = _header[2]
                    _recCommand = _header[3]
                    _recLen = _header[4]
                    for i in range(1,5):
                        _recCalcCS += _header[i]
                    _recPhase = 1
                    _recPos = 0
                    
                    if _recStation != _station:
                        reset()
                        continue;

                    if _recLen == 0:
                        _recPhase = 2

                    if _recLen > MAX_MESSAGE:
                       _recPhase = 0
                continue;
            if _recPhase == 1:
                _data[_recPos] = inch
                _recPos = _recPos+1
                _recCalcCS += inch;
                if _recPos == _recLen:
                    _recPhase = 2
                continue;
            if _recPhase == 2:
                if inch == ETX:
                    _recPhase = 3
                else:
                    reset();
                continue;
            if _recPhase == 3:
                _recCS = inch
                _recPhase = 4
                continue;
            if _recPhase == 4:
                if inch == EOT:
                    if _recCS == _recCalcCS%256:
                        if _save[_recSender-1] != _data[1]:
                            if _data[1] == 48:
                                _inSeat -= 1
                            else:
                                _inSeat += 1
                            print(_inSeat)
                            _save[_recSender-1] = _data[1]
                            try:
                                number = numberOfAvailableSlot - _inSeat
                                sql = "update park set numOfAvailableSlot = '%d' where parkId= '%s'" % (number, parkId)
                                print("Update availableSlot %d" %(number))
                                cursor.execute(sql)
                                db.commit()
                            except (MySQLdb.Error, MySQLdb.Warning) as e:
                                print(e)
                                db.rollback()
                reset();
                continue;
    except:
        print("Unexpected error:", sys.exc_info()[0])
        port.close()
##    while True:
##        numberOfNotAvailableSlot = readFromRS485()
##        numberOfAvailableSlotTemp = numberOfSlot - numberOfNotAvailableSlot
##        if numberOfAvailableSlotTemp != numberOfAvailableSlot:
##            try:
##                sql = "update park set numOfAvailableSlot = '%d' where parkId= '%s'" % (numberOfAvailableSlot) % (
##                    parkId)
##                print(sql)
##                cursor.execute(sql)
##                db.commit()
##            except (MySQLdb.Error, MySQLdb.Warning) as e:
##                print(e)
##                db.rollback()
        # end if
    # end while
    return