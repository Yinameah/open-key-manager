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

import threading
import queue
import time
import logging
import sys


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            new_instance = super(Singleton, cls).__call__(*args, **kwargs)
            new_instance._instances = cls._instances
            cls._instances[cls] = new_instance
        return cls._instances[cls]


class ArduinoCrawler(metaclass=Singleton):

    """Un thread qui poll les arduino pour savoir si on badge"""

    def __init__(self, virtual=False, virtual_arduinos=None):
        """
        Initialisation du crawler
        C'est un singleton qui expose une queue (self.queue) qui 
        contient les events de badge qui proviennent des arduinos
        """

        self.queue = queue.Queue()

        self.loop_flag = threading.Event()

        if virtual:
            if virtual_arduinos is None:
                logging.fatal("Try to start a virtual crawler without virtual arduinos")
                sys.exit()
            else:
                self.virtual_arduinos = virtual_arduinos

            t = threading.Thread(name="ArduinoCrawler", target=self.virtual_loop)
        else:
            t = threading.Thread(name="ArduinoCrawler", target=self.loop)

        t.start()

    def virtual_loop(self):

        print("Start virtual polling loop")

        while not self.loop_flag.is_set():

            for a in self.virtual_arduinos:
                arduino_id, current_key = a.poll()
                # TODO : continuer ici :
                # Il faut foutre ces infos en DB, voir s'il faut un lock ou
                # si on récupère la queueu ailleurs, etc ...
                self.queue.put(arduino_id, current_key)

                time.sleep(0.2)

    def loop(self):

        while not self.loop_flag.is_set():
            print("Polling des vrais arduino, not implemented yet ...")
            time.sleep(1)

    def stop(self):
        self.loop_flag.set()
