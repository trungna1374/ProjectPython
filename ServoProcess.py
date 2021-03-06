import RPi.GPIO as GPIO


def init():
    global pwm1
    global pwm2
    GPIO.setup(17, GPIO.OUT)
    GPIO.setup(18, GPIO.OUT)
    pwm1 = GPIO.PWM(17, 50)
    pwm2 = GPIO.PWM(18, 50)
    pwm1.start(15)
    pwm2.start(10)
    return


def liftUp1():
    pwm1.ChangeDutyCycle(7.5)
    return


def liftOff1():
    pwm1.ChangeDutyCycle(15)
    return


def liftUp2():
    pwm2.ChangeDutyCycle(5.5)
    return


def liftOff2():
    pwm2.ChangeDutyCycle(10)
    return

