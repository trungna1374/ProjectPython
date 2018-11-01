import serial
import MySQLdb

port = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=0.2)
db = MySQLdb.connect("localhost", "root", "admin123", "iot")
cursor = db.cursor()
parkId = "p1"
numberOfSlot = 0
numberOfAvailableSlot = 0
numberOfIncome = 0


def init():
    try:
        sql = "select * from park where parkId= '%s'" % (parkId)
        print(sql)
        cursor.execute(sql)
        data = cursor.fetchall()
        row = data[0]
        print(row)
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
    return


def readFromRS485():
    rcv = port.readline()
    print(rcv)
    return


def updateAvailableSlotToDB():
    init()
    seat = [numberOfSlot]
    while True:
        numberOfNotAvailableSlot = readFromRS485()
        numberOfAvailableSlotTemp = numberOfSlot - numberOfNotAvailableSlot
        if numberOfAvailableSlotTemp != numberOfAvailableSlot:
            try:
                sql = "update park set numOfAvailableSlot = '%d' where parkId= '%s'" % (numberOfAvailableSlot) % (
                    parkId)
                print(sql)
                cursor.execute(sql)
                db.commit()
            except (MySQLdb.Error, MySQLdb.Warning) as e:
                print(e)
                db.rollback()
        # end if
    # end while
    return
