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

from okm.backend.arduino_crawler import ArduinoCrawler

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
        for i in range(n):
            virt_arduino = VirtualArduino(i)
            self.arduinos.append(virt_arduino)
            self.arduino_combobox.Append(f"Arduino{virt_arduino.id}")

    def onBadge(self, event):
        n = self.arduino_combobox.GetSelection()
        key_id, name = self.key_combobox.GetValue().split(" (")
        name = name.strip(")")
        self.arduinos[n].badge(key_id)


class VirtualArduino:

    """Virtual arduino for dev purposes"""

    def __init__(self, uid):
        """Init a virtual arduino """

        self.current_key = None
        self.id = uid

    def badge(self, key_id):
        """
        Simule l'action de badger sur un arduino
        """
        logging.info(f"got badge {key_id}")

        if self.current_key is None:
            logging.info(f"Activation de l'arduino {self.id} pour clé {key_id}")
            self.current_key = key_id
        else:
            if key_id == self.current_key:
                logging.info(f"Deactivate plug")
                self.current_key = None
            else:
                logging.info(f"Already on for other user, do nothing")

    def poll(self):
        """
        Simule le polling du raspy sur l'arduino
        """
        return self.id, self.current_key

    def __str__(self):
        return f"< VirtualArduino object with id : {self.id} >"


if __name__ == "__main__":

    app = wx.App()
    frm = SimulatorWindow(None)
    app.MainLoop()
