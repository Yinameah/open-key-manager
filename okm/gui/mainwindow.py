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


class MainWindow(wx.Frame):
    """ 
    Main Window of the software
    """

    def __init__(self, *args, **kw):
        super(MainWindow, self).__init__(*args, **kw)

        self.MinSize = (300, 200)

        icon_uri = Path(__file__).parent.parent / "rsc/logo.png"
        img = wx.Icon()
        img.LoadFile(icon_uri.__str__(), wx.BITMAP_TYPE_ANY)
        self.SetIcon(img)

        self._makeMenuBar()
        self._makeLayout()

        self.CreateStatusBar()
        self.SetStatusText("Bienvenue")

        self.Show()

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

        vue1 = viewMenu.Append(wx.ID_ANY, "Vue 1", kind=wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.onVue1, vue1)

        vue2 = viewMenu.Append(wx.ID_ANY, "Vue 2", kind=wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.onVue2, vue2)

        vue3 = viewMenu.Append(wx.ID_ANY, "Vue 3", kind=wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.onVue3, vue3)

        menuBar.Append(viewMenu, "&Vues")

        ######################
        # M Gestion clés
        ######################
        keysMenu = wx.Menu()

        new_key = keysMenu.Append(wx.ID_ANY, "Ajouter une nouvelle clé")
        self.Bind(wx.EVT_MENU, self.onNewKey, new_key)
        modif_key = keysMenu.Append(wx.ID_ANY, "Gérer les accès d'une clé")
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

        # self.SetMenuBar(menuBar)

    def _makeLayout(self):
        """ Main Layout """

        self.main_panel = wx.Panel()
        sizer = wx.BoxSizer()

        self.txt = wx.TextCtrl(self)

        sizer.Add(self.txt, border=15, proportion=1, flag=wx.EXPAND | wx.ALL)

        self.SetSizer(sizer)

    def onVue1(self, event):
        print("Vue1 activée")

    def onVue2(self, event):
        print("Vue2 activée")

    def onVue3(self, event):
        print("Vue3 activée")

    def onNewKey(self, event):
        print("Nouvelle clé")

    def onModifKey(self, event):
        print("Éditer une clé")

    def onExit(self, event):
        """
        Close frame, end application
        """
        self.Close()

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


if __name__ == "__main__":

    app = wx.App()
    frm = MainWindow(None, title="Open Key Manager")
    app.MainLoop()
