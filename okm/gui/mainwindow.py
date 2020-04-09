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

from okm.backend.arduino_crawler import ArduinoCrawler
from okm.gui.newkeydialog import NewKeyDialog
from okm.gui.editkeydialog import EditKeyDialog
from okm.glob import DB_PATH


class MainWindow(wx.Frame):
    """ 
    Main Window of the software
    """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        self.MinSize = (300, 200)

        icon_uri = Path(__file__).parent.parent / "rsc/logo.png"
        img = wx.Icon()
        img.LoadFile(icon_uri.__str__(), wx.BITMAP_TYPE_ANY)
        self.SetIcon(img)

        self._makeMenuBar()
        self._makeLayout()

        self.SetTitle("Open Key Manager")

        self.CreateStatusBar()
        self.SetStatusText("Bienvenue")

        self.Bind(wx.EVT_CLOSE, self.OnCloseMainWindow, self)

        self.Show()

        self.crawler = ArduinoCrawler()

    def _makeMenuBar(self):
        """ Menu of application """

        menuBar = wx.MenuBar()

        ######################
        # M Fichier
        ######################
        fileMenu = wx.Menu()

        exitItem = fileMenu.Append(wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.onExit, exitItem)

        menuBar.Append(fileMenu, "&File")

        ######################
        # M Vue
        ######################
        viewMenu = wx.Menu()

        vue1 = viewMenu.Append(wx.ID_ANY, "Vue &1", kind=wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.onVue1, vue1)

        vue2 = viewMenu.Append(wx.ID_ANY, "Vue &2", kind=wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.onVue2, vue2)

        vue3 = viewMenu.Append(wx.ID_ANY, "Vue &3", kind=wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.onVue3, vue3)

        menuBar.Append(viewMenu, "&Vues")

        ######################
        # M Gestion clés
        ######################
        keysMenu = wx.Menu()

        new_key = keysMenu.Append(wx.ID_ANY, "Ajouter une &nouvelle clé")
        self.Bind(wx.EVT_MENU, self.onNewKey, new_key)
        modif_key = keysMenu.Append(wx.ID_ANY, "&Gérer les accès d'une clé")
        self.Bind(wx.EVT_MENU, self.onModifKey, modif_key)

        menuBar.Append(keysMenu, "Gestion des &clés")

        ######################
        # M About
        ######################
        helpMenu = wx.Menu()

        aboutItem = helpMenu.Append(wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.onAbout, aboutItem)

        menuBar.Append(helpMenu, "&Help")

        self.SetMenuBar(menuBar)

    def _makeLayout(self):
        """ Main Layout """

        # Note à moi-même :
        # var = wx.Panel(self) ici suffit à foutre le panel.
        # Mais s'il y en a plusieurs, alors il faut passer un sizer plutôt, sinon
        # la taille du panel est ingérable
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.vues = [Vue1(self), Vue2(self), Vue3(self)]
        for vue in self.vues:
            sizer.Add(vue, flag=wx.EXPAND | wx.ALIGN_CENTER)

        # J'imagine que s'il y a qu'un seul enfant, setsizer est appelé en interne
        self.SetSizer(sizer)

        self.showVue(0)

    def onVue1(self, event):
        self.showVue(0)

    def onVue2(self, event):
        self.showVue(1)

    def onVue3(self, event):
        self.showVue(2)

    def showVue(self, n):
        for i, vue in enumerate(self.vues):
            if i == n:
                vue.Show()
                # vue.Fit()
                self.Layout()
            else:
                vue.Hide()

    def onNewKey(self, event):
        dlg = NewKeyDialog(self)
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            key_id = dlg.key_id.GetValue()
            name = dlg.name.GetValue()
            surname = dlg.surname.GetValue()
            email = dlg.email.GetValue()
            phone = dlg.phone.GetValue()

            new_data = (key_id, name, surname, email, phone)

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO keys VALUES (?, ?, ?, ?, ?)", new_data)
            conn.commit()
            conn.close()

    def onModifKey(self, event):
        dlg = EditKeyDialog(self)
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            key_id = dlg.key_combobox.id[dlg.key_combobox.GetValue()]

            # conn.set_trace_callback(print)
            for a_id in dlg.arduinos_cb:
                c.execute(
                    f"""UPDATE perms SET '{a_id}'=? WHERE key_id=?""",
                    (dlg.arduinos_cb[a_id].GetValue(), key_id),
                )
            conn.commit()
            conn.close()

    def onExit(self, event):
        """
        Close frame, end application
        """
        self.Close()

    def OnCloseMainWindow(self, event):
        """
        React to close event
        """
        self.crawler.stop()
        event.Skip()

    def onAbout(self, event):
        """
        Display about popup
        """
        msg = """
OPEN KEY MANAGER
A rfid key manager based on RaspberryPi and Arduinos

Copyright © 2020 Aurélien Cibrario

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

        wx.MessageBox(
            msg, "À propos", wx.OK | wx.ICON_INFORMATION,
        )


class Vue1(wx.Panel):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.txt = wx.TextCtrl(self)
        self.txt2 = wx.TextCtrl(self)

        sizer.Add(self.txt, border=15, proportion=3, flag=wx.ALL)
        sizer.Add(self.txt2, border=15, proportion=1, flag=wx.EXPAND | wx.ALL)

        self.SetSizer(sizer)

        self.BackgroundColour = wx.RED


class Vue2(wx.Panel):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.txt = wx.StaticText(self, label="Un label")

        sizer.Add(self.txt, border=15, proportion=1, flag=wx.EXPAND | wx.ALL)

        self.SetSizer(sizer)


class Vue3(wx.Panel):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn = wx.Button(self, label="Un label pour bouton")

        sizer.Add(self.btn, border=15, proportion=1, flag=wx.EXPAND | wx.ALL)

        self.SetSizer(sizer)


if __name__ == "__main__":

    app = wx.App()
    frm = MainWindow(None)
    app.MainLoop()
