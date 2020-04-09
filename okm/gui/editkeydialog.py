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

import sqlite3

try:
    import validators
except ImportError as e:
    from okm.gui import validators

try:
    from okm.glob import DB_PATH, ARDUINOS_DESC
except ImportError:
    from pathlib import Path

    DB_PATH = "/home/aurelien/sketchbook/open-key-manager/okm/db.sqlite3"
    ARDUINOS_DESC = {"10": "bla", "20": "bli", "30": "blou"}


class EditKeyDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super().__init__(*args, style=wx.DEFAULT_DIALOG_STYLE, **kw)

        self.SetTitle("Éditer une clé")

        self.MinSize = (250, 100)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.key_combobox = wx.ComboBox(self, style=wx.CB_READONLY)
        sizer.Add(self.key_combobox, border=5, flag=wx.ALL | wx.EXPAND)
        self.key_combobox.Bind(wx.EVT_COMBOBOX, self.onComboChange, self.key_combobox)

        # {'arduino_id':'wx.Checkbox', ... }
        self.arduinos_cb = {}
        for a_id, desc in ARDUINOS_DESC.items():
            cb = wx.CheckBox(self, label=desc)
            sizer.Add(cb, border=5, flag=wx.ALL | wx.ALIGN_CENTER)
            self.arduinos_cb[a_id] = cb

        self.populate_keys()

        btns = self.CreateSeparatedButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(btns, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)

        self.SetSizerAndFit(sizer)

    def populate_keys(self):

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM keys")
        r = c.fetchall()
        conn.close()

        # wx.Combobox.id = {'full_name':'key_id', ... }
        self.key_combobox.id = {}
        for line in r:
            full_name = f"{line['name']} {line['surname']}"
            self.key_combobox.Append(full_name)
            self.key_combobox.id[full_name] = line["key_id"]

        self.key_combobox.Select(0)
        self.onComboChange()

    def onComboChange(self, *event):

        full_name = self.key_combobox.GetValue()

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT * FROM perms WHERE key_id=?", (self.key_combobox.id[full_name],)
        )
        # key_id is UNIQUE, so fetchone() makes sense
        r = c.fetchone()
        conn.close()

        for a_id in self.arduinos_cb:
            if r[a_id] == 0:
                self.arduinos_cb[a_id].SetValue(False)
            else:
                self.arduinos_cb[a_id].SetValue(True)


if __name__ == "__main__":

    app = wx.App()
    frm = wx.Frame(None)
    frm.Show()
    dial = EditKeyDialog(frm)
    result = dial.ShowModal()

    print(result)

    app.MainLoop()
