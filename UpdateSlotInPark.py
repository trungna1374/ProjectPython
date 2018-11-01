import serial
import MySQLdb

#port = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=0.2)
db = MySQLdb.connect("localhost", "root", "Hehe@123", "smart_parking")
cursor = db.cursor()
parkId = "p1"
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


def updateAvailableSlotToDB():
    init()
    print(numberOfSlot)
    seat = [numberOfSlot]
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
