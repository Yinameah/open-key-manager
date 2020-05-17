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
import datetime
import sqlite3

try:
    from okm.glob import DB_PATH, LOCK
    import okm.glob as glob
    from okm.backend.arduinos import get_arduinos
    from okm.utils import DbCursor
except ImportError:
    logging.fatal("okm not importable here. Might be a problem")


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

    def __init__(self):
        """
        Initialisation du crawler
        C'est un singleton qui cause aux arduinos et gère les lock/unlocks
        """

        self.loop_flag = threading.Event()

        # [arduinoInstance, ... ]
        self.arduinos = get_arduinos()

        #########################################################
        # The following properties are API. Use with okm.glob.LOCK
        # Both from inside and outside
        #########################################################

        # {'arduino_id': 'unlock_key', ... }
        # with 'unlock_key' == 'key_id' | None if locked
        self.arduinos_states = {a.id: None for a in self.arduinos}

        # {'unknown_key', 'key_id',
        #
        # }
        self.mainwindow_notify = {}

        t = threading.Thread(name="ArduinoCrawler", target=self.loop)
        t.start()

    def loop(self):

        print("Start crawler loop")

        while not self.loop_flag.is_set():
            ############################################$
            # En gros, dans ce loop sur les arduinos :
            # - On essaie de recevoir un message. Si None : on passe
            # - Si on a new_read:XXXX , XXXX est l'id de la clé, et on compare en DB
            # - En envoie à l'arduine l'ordre pertinent :
            #   order:lock | order:unlock | order:denied
            # - Après envoi d'ordre, la fonction est bloquante jusqu'à reçevoir une réponse
            # - Si la réponse est correcte, on effectue les incriptions en DB
            ############################################$
            for a in self.arduinos:

                msg_in = a.recv_message()

                if msg_in is None:
                    continue

                msg_in = msg_in.split(":")
                if len(msg_in) == 2:
                    if msg_in[0] == "new_read":
                        request_key = msg_in[1]
                    else:
                        continue
                else:
                    continue

                with DbCursor() as c:
                    c.execute("SELECT * FROM perms WHERE key_id=?", (request_key,))
                    # key_id is UNIQUE, so fetchone() makes sense
                    r = c.fetchone()

                try:
                    r[str(a.id)]
                except TypeError:
                    logging.warning(
                        "Seems like an unknown key is used."
                        " Notify windows and reject"
                    )
                    with LOCK:
                        self.mainwindow_notify["unknown_key"] = request_key
                    a.send_message("order:denied;")
                    continue

                if r[str(a.id)] == 1:
                    print("Cet utilisateur a le droit d'ouvrir cet arduino. Départ")
                    timestamp = datetime.datetime.now()

                    if self.arduinos_states[a.id] == None:

                        print("On essaie de déverouiller")
                        a.send_message("order:unlock")
                        lock_state = "unlocked;"

                        if is_answer(a, "confirm:unlock"):
                            with DbCursor() as c:
                                c.execute(
                                    "INSERT INTO stamps VALUES (?, ?, ?, ?)",
                                    (request_key, a.id, timestamp, lock_state),
                                )
                            with LOCK:
                                self.arduinos_states[a.id] = request_key
                            print("Le déverrouillage est un succès")
                        else:
                            print("Déverouillage pas marche")
                            # Prevent unwanted unlock
                            a.send_message("order:lock;")

                    elif self.arduinos_states[a.id] == request_key:

                        print("Même user, on essaye de reverouiller")
                        a.send_message("order:lock;")
                        lock_state = "locked"

                        if is_answer(a, "confirm:lock"):
                            with DbCursor() as c:
                                c.execute(
                                    "INSERT INTO stamps VALUES (?, ?, ?, ?)",
                                    (request_key, a.id, timestamp, lock_state),
                                )
                            with LOCK:
                                self.arduinos_states[a.id] = None
                            print("Reverouillage effectué")
                        else:
                            print("Reverouillage pas marche")
                            # Prevent unwanted lock
                            a.send_message("order:unlock;")

                    else:
                        print("Déjà utilisé par quelqu'un d'autre ...")
                        a.send_message("order:denied")

                else:
                    print("Verboooten !")
                    a.send_message("order:denied")

            # FIXME : quasi sûr que ce sera contre productif quand on aura plusieurs arduinos
            time.sleep(0.2)

    def stop(self):
        for a in self.arduinos:
            a.stop()
        self.loop_flag.set()


def is_answer(arduino, answer, timeout=2):
    """
    Wait for an answer of arduino for givent timeout

    :return Bool
    """
    start_time = time.monotonic()
    msg = None
    success = False

    while start_time + timeout > time.monotonic() and not success:

        msg = arduino.recv_message()

        if msg is not None:
            if answer in msg:
                success = True

    return success


if __name__ == "__main__":

    class MocArduino:
        def recv_message(self):
            return "test"

    print(is_answer(MocArduino(), "test"))
