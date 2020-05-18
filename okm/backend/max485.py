# -*- coding: utf-8 -*-
#
# This file is part of the Open Key Managment
# A rfid key manager system based on raspberryPi and Arduino
#
# Copyright 2020 Aurélien Cibrario <aurelien.cibrario@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import RPi.GPIO as gpio
import serial
import time
import logging


# class Singleton(type):
#     """
#     A simple Singleton implementation.
#     Use with :
#     class MyClass(metaclass=Singleton):
#     """

#     _instances = {}

#     def __call__(cls, *args, **kwargs):
#         if cls not in cls._instances:
#             new_instance = super(Singleton, cls).__call__(*args, **kwargs)
#             new_instance._instances = cls._instances
#             cls._instances[cls] = new_instance
#         return cls._instances[cls]


class Max485:

    # FIXME : only one pin is needed. To be updated on new hardware version
    RE_PIN = 23
    DE_PIN = 4

    rsp_pending_for_id = None
    pending_rsp = None

    gpio.setmode(gpio.BCM)

    # FIXME : This produces error. Maybe is not needed ...
    gpio.setup(RE_PIN, gpio.OUT)
    gpio.setup(DE_PIN, gpio.OUT)

    @classmethod
    def send_message(cls, a_id, msg):
        _, order = msg.split(":")
        rsp = cls.poll(a_id, order)
        cls.rsp_pending_for_id = a_id
        cls.pending_rsp = rsp

    @classmethod
    def recv_message(cls, a_id):
        if cls.rsp_pending_for_id is None:
            # try to get new read for a_id
            rsp = cls.ask_for_new_read(a_id)
            return rsp
        else:
            if cls.rsp_pending_for_id == a_id:
                # return pending answer
                pending_rsp = cls.pending_rsp
                cls.pending_rsp = None
                cls.rsp_pending_for_id = None

                return pending_rsp
            else:
                # this should not occur, since crawler waits for answer after an order
                logging.fatal(
                    f"Trying to read a message on a RS485 arduino {a_id}"
                    f" while order in pending for {order_pending_for_id}"
                )
                return None

    @classmethod
    def ask_for_new_read(cls, a_id):
        """
        Ask arduino with given id for new read over 485
        
        :a_id: (int) id of arduino to ask
        """
        return cls.poll(a_id, "ask_for_new")

    @classmethod
    def poll(cls, a_id, order):
        """
        The send, wait and receive mechanisme via RS485 is implemented here

        :a_id: (int) the id of arduino to poll
        :order: (str) the message to poll arduino with, aka order
        """

        with serial.Serial("/dev/ttyAMA0", 9600, timeout=2) as ser:

            cls.set_send_mode()

            msg = f"{a_id}:{order};"
            msg = msg.encode()
            ser.write(msg)
            logging.info(f"<-- {msg}")
            # wait 20ms to allow message to be transmitted
            time.sleep(0.02)

            # Wait for answer
            cls.set_receive_mode()
            rsp = ser.read_until(b";")

            logging.info(f"--> {rsp}")

            # FIXME Will not be needed when multiple devices
            # wait 30ms to be shure device is ready to receive again
            time.sleep(0.03)
            time.sleep(0.1)

        return rsp.decode().strip(";")

    @classmethod
    def set_send_mode(cls):
        gpio.output(cls.RE_PIN, 1)
        gpio.output(cls.DE_PIN, 1)

    @classmethod
    def set_receive_mode(cls):
        gpio.output(cls.RE_PIN, 0)
        gpio.output(cls.DE_PIN, 0)


if __name__ == "__main__":

    while True:
        Max485.ask_for_new_read(20)

        time.sleep(0.5)
