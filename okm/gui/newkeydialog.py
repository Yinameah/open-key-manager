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


class NewKeyDialog(wx.Dialog):
    def __init__(self, *args, **kw):

        try:
            new_key = kw["new_key"]
        except KeyError as e:
            new_key = None
        else:
            # If left behind, breaks wx call ...
            del kw["new_key"]

        super().__init__(*args, style=wx.DEFAULT_DIALOG_STYLE, **kw)

        self.SetTitle("Ajouter une nouvelle clé")

        fields = wx.FlexGridSizer(2, gap=(30, 5))

        txt = wx.StaticText(self, label="ID de la clé :")
        fields.Add(txt, flag=wx.ALL, border=10)
        self.key_id = wx.TextCtrl(
            self,
            name="id clé",
            validator=validators.EnterSomethingValidator(),
            size=(250, -1),
        )
        if new_key is not None:
            self.key_id.SetValue(new_key)
        fields.Add(self.key_id, flag=wx.ALL, border=8)

        txt = wx.StaticText(self, label="Prénom :")
        fields.Add(txt, flag=wx.ALL, border=10)
        self.name = wx.TextCtrl(
            self, name="prénom", validator=validators.EnterSomethingValidator()
        )
        fields.Add(self.name, flag=wx.EXPAND | wx.ALL, border=8)

        txt = wx.StaticText(self, label="Nom de famille :")
        fields.Add(txt, flag=wx.ALL, border=10)
        self.surname = wx.TextCtrl(
            self, name="nom de famille", validator=validators.EnterSomethingValidator()
        )
        fields.Add(self.surname, flag=wx.EXPAND | wx.ALL, border=8)

        txt = wx.StaticText(self, label="E-mail :")
        fields.Add(txt, flag=wx.ALL, border=10)
        self.email = wx.TextCtrl(
            self, name="e-mail", validator=validators.EnterSomethingValidator()
        )
        fields.Add(self.email, flag=wx.EXPAND | wx.ALL, border=8)

        txt = wx.StaticText(self, label="Téléphone :")
        fields.Add(txt, flag=wx.ALL, border=10)
        self.phone = wx.TextCtrl(
            self, name="téléphone", validator=validators.EnterSomethingValidator()
        )
        fields.Add(self.phone, flag=wx.EXPAND | wx.ALL, border=8)

        sizer = wx.BoxSizer(wx.VERTICAL)
        btns = self.CreateSeparatedButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(fields, flag=wx.ALL, border=3)
        sizer.Add(btns, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)

        self.SetSizerAndFit(sizer)


if __name__ == "__main__":

    app = wx.App()
    frm = wx.Frame(None)
    frm.Show()
    dial = NewKeyDialog(frm)
    result = dial.ShowModal()
    print(result)

    app.MainLoop()
