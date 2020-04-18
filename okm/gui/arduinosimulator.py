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
from okm.backend.arduinos import get_arduinos
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

        button = wx.Button(self, label="Reload Users")
        sizer.Add(button, pos=(2, 2))
        self.Bind(wx.EVT_BUTTON, self.populate_keys, button)

        # {'desc': <VirtualArduino>, ... }
        self.arduinos = {}
        self.make_arduinos(3)
        self.arduino_combobox.Select(0)

        self.populate_keys()

        self.SetSizer(sizer)
        self.Show()

    def populate_keys(self, *event):

        self.key_combobox.Clear()

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
        all_arduinos = get_arduinos()
        for arduino in all_arduinos:
            if arduino.type == "virtual":
                virt_arduino = arduino
                virt_arduino.send("init")
                self.arduinos[desc] = virt_arduino
                self.arduino_combobox.Append(virt_arduino.desc)

    def onBadge(self, event):
        a_desc = self.arduino_combobox.GetValue()
        key_id, name = self.key_combobox.GetValue().split(" (")
        name = name.strip(")")
        self.arduinos[a_desc].badge(key_id)


if __name__ == "__main__":

    app = wx.App()
    frm = SimulatorWindow(None)
    app.MainLoop()
