import serial
import time
from serial.tools import list_ports

import RPi.GPIO as gpio


RE_PIN = 23
DE_PIN = 4

gpio.setmode(gpio.BCM)

gpio.setup(RE_PIN, gpio.OUT)
gpio.setup(DE_PIN, gpio.OUT)


def set_send_mode():
    gpio.output(RE_PIN, 1)
    gpio.output(DE_PIN, 1)


def set_receive_mode():
    gpio.output(RE_PIN, 0)
    gpio.output(DE_PIN, 0)


with serial.Serial("/dev/ttyAMA0", 9600, timeout=5) as ser:
    i = 0
    while True:
        set_send_mode()
        msg = f"bidule:machin{i};"
        i += 1

        msg = msg.encode()
        ser.write(msg)
        print(f"--> {msg}")
        # wait 20ms to allow message to be transmitted
        time.sleep(0.02)

        # Wait for answer
        set_receive_mode()
        rsp = ser.read_until(b";")

        print(f"<-- {rsp}")
        set_send_mode()

        # wait 20ms before starting a new loop
        # otherwise arduino is not ready to receive
        time.sleep(0.02)
