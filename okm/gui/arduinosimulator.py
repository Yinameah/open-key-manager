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


import wx

from pathlib import Path
import sqlite3
import queue
import argparse
import logging
import threading
import time

from okm.backend.arduino_crawler import ArduinoCrawler
from okm.glob import DB_PATH, ARDUINOS_DESC

DB_PATH = Path(__file__).parent.parent / "db.sqlite3"


class SimulatorWindow(wx.Frame):
    """ 
    A windows to simulate arduino badging for developpment purposes
    """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self.SetTitle("Arduino Simulator")
        self.MinSize = (250, 100)

        sizer = wx.GridBagSizer(vgap=3, hgap=3)
        sizer.AddGrowableCol(0, 1)

        self.arduino_combobox = wx.ComboBox(self, style=wx.CB_READONLY)
        sizer.Add(self.arduino_combobox, pos=(0, 0), span=(0, 1), flag=wx.EXPAND)

        self.key_combobox = wx.ComboBox(self, style=wx.CB_READONLY)
        sizer.Add(self.key_combobox, pos=(1, 0), span=(0, 1), flag=wx.EXPAND)

        button = wx.Button(self, label="Badger !")
        sizer.Add(button, pos=(0, 2), flag=wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.onBadge, button)

        self.arduinos = []
        self.make_arduinos(3)
        self.arduino_combobox.Select(0)

        self.populate_keys()

        self.SetSizer(sizer)
        self.Show()

    def populate_keys(self):

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM keys")
        r = c.fetchall()
        conn.close()

        for line in r:
            self.key_combobox.Append(
                f"{line['key_id']} ({line['name']} {line['surname']})"
            )

        self.key_combobox.Select(0)

    def make_arduinos(self, n):
        for a_id, desc in ARDUINOS_DESC.items():
            virt_arduino = VirtualArduino(a_id, desc)
            self.arduinos.append(virt_arduino)
            self.arduino_combobox.Append(f"Arduino{virt_arduino.id}")

    def onBadge(self, event):
        n = self.arduino_combobox.GetSelection()
        key_id, name = self.key_combobox.GetValue().split(" (")
        name = name.strip(")")
        self.arduinos[n].badge(key_id)


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

    def __init__(self, uid, desc):
        """Init a virtual arduino """

        self.id = uid
        self.desc = desc

        self.pending_key_id = None
        self.is_open = False
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

    def poll(self):
        """
        Simule le polling du raspy sur l'arduino

        :return: (id, pending_key_id)
        :id: (str) ID de l'arduino
        :pending_key_id: (str) ID de la clé, None if no badge
        """
        return self.id, self.pending_key_id

    def send(self, order):
        """
        Simule l'envoi d'un ordre à l'arduino

        :order: (str) can be "open", "close", "ignore", "init"
        """
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

    def __str__(self):
        return f"< VirtualArduino object with id : {self.id} >"


if __name__ == "__main__":

    app = wx.App()
    frm = SimulatorWindow(None)
    app.MainLoop()
