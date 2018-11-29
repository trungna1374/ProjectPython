import serial
port = serial.Serial("/dev/ttyUSB0",baudrate=115200)
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
_station=1

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
  
try:
    _inSeatSave=0
    _inSeat=0
    print("start")
    while True:
        print(_inSeat)
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
                if _recCS == _recCalcCS:
                    if _save[_recSender-1] != _data[1]:
                        if _data[1] == 48:
                            _inSeat -= 1
                        else:
                            _inSeat += 1
                        _save[_recSender-1] = _data[1]
            reset();
            continue;
except:
    print("Unexpected error:", sys.exc_info()[0])
    port.close()
