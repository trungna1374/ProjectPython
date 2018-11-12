import RPi.GPIO as GPIO
def init():
    global pwm
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(11,GPIO.OUT)
    pwm = GPIO.PWM(11,50)
    pwm.start(15)
    return
def pullUp():
    pwm.ChangeDutyCycle(7.5)
    return


def liftOff():
    pwm.ChangeDutyCycle(15)
    return


def servoProcess():
    init()
    return
