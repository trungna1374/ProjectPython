import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(23,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(24,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while True:
##    print(GPIO.input(20))
    print(GPIO.input(23))
