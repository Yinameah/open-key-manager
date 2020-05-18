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

try:
    import okm.glob as glob
    from okm.backend.max485 import Max485
except ImportError as e:
    import sys

    sys.path.append("/home/aurelien/sketchbook/open-key-manager")
    import okm.glob as glob
    from okm.backend.max485 import Max485

import serial
from serial.tools import list_ports
import logging
import time
import threading
import queue

"""
In this module, we defines arduinos

Allow to have various ways of comminication with differents arduinos

Each class of device MUST implement an id property, which correspond to
ARDUINOS_DESC déclaration in okm.glob

MUST also implement API of crawler, nocitabley, recv_message & send_message

"""


def get_arduinos():
    """
    Return a list of arduinos
    """

    ###################################################
    # List of devices to read keys from
    # Various classes (type of devices) can be initialized
    # The crawler will loop over them and send/receive messages
    ###################################################
    arduinos = [
        USBArduino(10, "85735313932351B011E2"),
        RS485Arduino(20),
        # FIXME VirtualArdino doesn't respect API anymore. Update if needed
        # VirtualArduino(30),
    ]

    # Imprimante 3d ...
    # arduinos.append(....

    return arduinos


class USBArduino:
    def __init__(self, a_id, serial_number):

        # id of arduino
        self.id = a_id

        # name of arduino
        self.name = glob.ARDUINOS_DESC[self.id]

        self.serial_device = None

        self.type = "usb"

        for p in list_ports.comports():
            if p.serial_number == serial_number:
                self.serial_device = p.device
        if self.serial_device is None:
            raise RuntimeError(
                f"Arduino with serial_number : {serial_number} not found"
            )

        self.loop_flag = threading.Event()
        t = threading.Thread(name=f"USBArduino {serial_number} loop", target=self.loop)

        self._send_queue = queue.Queue(maxsize=1)
        self._recv_queue = queue.Queue()

        t.start()

    def loop(self):

        with serial.Serial(self.serial_device, 115200, timeout=0.05) as ser:
            # Wait for device ready
            line = ""
            while not "confirm:ready" in line:
                line = ser.read_until(";").decode()

            while not self.loop_flag.is_set():

                if self._send_queue.empty():
                    line = ser.read_until(";").decode()
                    if line != "":
                        logging.info(f"{self} loop : arduino --> {line} ")
                        # remove ;
                        line = line[:-1]
                        self._recv_queue.put(line.strip())

                try:
                    line = self._send_queue.get(timeout=0.01)
                except queue.Empty as e:
                    pass
                else:
                    line += ";"
                    logging.info(f"{self} loop : arduino <-- {line} ")
                    ser.write(line.encode())

            print("end of loop")

    def stop(self):
        self.loop_flag.set()

    def send_message(self, msg):
        """ Send message to arduino """
        self._send_queue.put(msg, timeout=5)

    def recv_message(self):
        """ Receive message from arduino """
        try:
            msg = self._recv_queue.get(timeout=0.01)
        except queue.Empty as e:
            msg = None
        return msg

    def __str__(self):
        return f"< USBArduino, id:{self.id} >"


class RS485Arduino:
    def __init__(self, a_id):
        self.id = a_id

    def send_message(self, msg):
        """ Send message to arduino """
        Max485.send_message(self.id, msg)

    def recv_message(self):
        """ Receive message from arduino """
        # Try to get a new read
        new_read = Max485.recv_message(self.id)

        p1, p2 = new_read.split(":")

        if p1 == "new_read" and p2 == "none":
            return None
        else:
            return new_read

    def stop(self):
        pass


class VirtualArduino:

    """
    Virtual arduino for dev purposes

    Logique :
    1) Quand l'arduino détecte un badge, il stocke l'id de la clé et passe son 
        status à "wait_for_answer". Puis il start une loop d'attente
    2) Il attends d'être pollé par l'arduino. Il retourne les infos
        (l'id de la clé et l'id de l'Arduino)
    3) Quand il reçoit une réponse, il stocke l'action a effectuer dans son status
        ce qui a pour effet d'arrêter la boucle d'attente
    4) L'ordre est traité (ouverture/fermeture) et l'arduino revient à l'état d'origine
    """

    # FIXME VirtualArdino doesn't respect API anymore. Update if needed
    def __init__(self, uid):
        """Init a virtual arduino """

        self.id = uid
        self.desc = glob.ARDUINOS_DESC[uid]

        self.pending_key_id = None
        self.is_open = False

        self.type = "virtual"

        # 'idle' | 'wait_for_answer' | 'wait_to_open' | 'wait_to_close'
        self.status = "idle"

    def badge(self, key_id):
        """
        Simule l'action de badger sur un arduino
        """
        if self.status == "idle":

            logging.info(f"{self} got badge {key_id}")
            self.pending_key_id = key_id

            self.status = "wait_for_answer"

            def wait_for_answer():
                while self.status == "wait_for_answer":
                    time.sleep(0.2)

                if self.status == "wait_for_close":
                    print(f"{self} got order to close")
                    self.is_open = False

                if self.status == "wait_for_open":
                    print(f"{self} got order to open")
                    self.is_open = True

                self.status = "idle"
                self.pending_key_id = None

            logging.info(f"Start wait_for_answer loop")
            t = threading.Thread(name="Arduino wait_for_answer", target=wait_for_answer)
            t.start()

    def send_message(self, msg):
        """ Send message to arduino """
        if order == "init":
            self.is_open = False
            self.status = "idle"
        elif order == "ignore":
            self.status = "idle"
        else:
            if self.status == "wait_for_answer":
                with threading.Lock():
                    if order == "open":
                        self.status = "wait_for_open"
                    elif order == "close":
                        self.status = "wait_for_close"

    def recv_message(self):
        """ Receive message from arduino """
        if self.pending_key_id is None:
            return None

        return "new_read:" + self.pending_key_id

    def stop(self):
        pass

    def __str__(self):
        return f"< VirtualArduino, id : {self.id}, name : {self.name} >"


if __name__ == "__main__":

    usbarduino = usbarduino("10", "85735313932351b011e2")

    def rec():
        while true:
            msg_in = usbarduino.recv_message()
            if msg_in is not none:
                print("- - >", msg_in)
                msg_in = msg_in.split(":")
                if len(msg_in) == 2:
                    if msg_in[0] == "new_read":
                        if msg_in[1] == "d7425919":
                            msg_out = "d"
                            print("< - -", msg_out)
                            usbarduino.send_message(msg_out)

    t = threading.thread(target=rec)
    t.start()

    while true:
        i = input()

    usbarduino.stop()
    t._stop()
