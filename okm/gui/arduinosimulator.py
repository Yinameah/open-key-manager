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

from okm.backend.arduino_crawler import ArduinoCrawler

CRAWLER = ArduinoCrawler()


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

        self.SetSizer(sizer)
        self.Show()

        self.arduinos = []
        self.make_arduinos(3)
        self.arduino_combobox.Select(0)

    def make_arduinos(self, n):
        for i in range(n):
            virt_arduino = VirtualArduino(i)
            self.arduinos.append(virt_arduino)
            self.arduino_combobox.Append(f"Arduino{virt_arduino.id}")

    def onBadge(self, event):
        n = self.arduino_combobox.GetSelection()
        print(f"on badge sur {self.arduinos[n]}")
        CRAWLER.queue.put(self.arduinos[n].id)


class VirtualArduino:

    """Virtual arduino for dev purposes"""

    def __init__(self, uid):
        """Init a virtual arduino """

        self.is_on = False
        self.id = uid

    def got_badge(self):
        self.is_on = not self.is_on

    def __str__(self):
        return f"< VirtualArduino object with id : {self.id} >"


if __name__ == "__main__":

    app = wx.App()
    frm = SimulatorWindow(None)
    app.MainLoop()
