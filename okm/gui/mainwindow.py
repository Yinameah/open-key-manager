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
from wx import dataview

from pathlib import Path
import logging
import datetime
import sqlite3
import threading
import copy

from okm.backend.arduino_crawler import ArduinoCrawler
from okm.gui.newkeydialog import NewKeyDialog
from okm.gui.editkeydialog import EditKeyDialog
from okm.glob import DB_PATH, ARDUINOS_DESC, LOCK
import okm.glob
from okm.utils import DbCursor


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
        # Show before makeLayout to allow Vue0 update infos to start
        self.Show()
        self._makeLayout()

        self.SetTitle("Open Key Manager")

        self.CreateStatusBar()
        self.SetStatusText("Bienvenue")

        self.Bind(wx.EVT_CLOSE, self.OnCloseMainWindow, self)

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

        vue1 = viewMenu.Append(wx.ID_ANY, "Vue &1 - Live", kind=wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.onVue1, vue1)

        vue2 = viewMenu.Append(wx.ID_ANY, "Vue &2 - Recap", kind=wx.ITEM_RADIO)
        self.Bind(wx.EVT_MENU, self.onVue2, vue2)

        vue3 = viewMenu.Append(wx.ID_ANY, "Vue &3 - Log", kind=wx.ITEM_RADIO)
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
        sizer = wx.BoxSizer(wx.VERTICAL)
        flags = wx.SizerFlags(1).Expand().Border(wx.ALL, 10)

        self.vues = [Vue1(self), Vue2(self), Vue3(self)]
        for vue in self.vues:
            sizer.Add(vue, flags)

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
                vue.Fit()
                self.Layout()
                try:
                    vue.update_infos()
                except AttributeError:
                    pass
            else:
                try:
                    vue.timer.Stop()
                except AttributeError as e:
                    pass
                vue.Hide()

    def onNewKey(self, *event, **kw):

        new_key = kw.get("new_key", None)
        if new_key is None:
            dlg = NewKeyDialog(self)
        else:
            dlg = NewKeyDialog(self, new_key=new_key)
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
            c.execute("INSERT INTO perms VALUES (?, ?, ?, ?)", (key_id, 0, 0, 0))
            conn.commit()
            conn.close()

    def onModifKey(self, event):
        dlg = EditKeyDialog(self)
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            key_id = dlg.key_combobox.id[dlg.key_combobox.GetValue()]

            # conn.set_trace_callback(print)
            with DbCursor() as c:
                for a_id in dlg.arduinos_cb:
                    c.execute(
                        f"""UPDATE perms SET '{a_id}'=? WHERE key_id=?""",
                        (dlg.arduinos_cb[a_id].GetValue(), key_id),
                    )

    def onExit(self, event):
        """
        Close frame, end application
        """
        self.Close()

    def OnCloseMainWindow(self, event):
        """
        React to close event
        """
        ArduinoCrawler().stop()
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


def expanded(widget, padding=6):
    sizer = wx.BoxSizer()
    sizer.Add(widget, wx.ID_ANY, wx.EXPAND | wx.ALL, padding)
    return sizer


class Vue1(wx.Panel):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        # self.arduinos_live_infos = {
        #    {"arduino_id": {
        #        "key": "key_id" | None,
        #        "full_name": "Bli Blou",
        #    }}
        self.arduinos_live_infos = {a_id: {} for a_id in ARDUINOS_DESC}

        sizer = wx.GridSizer(4, 8, 8)

        font = self.GetFont()
        font.SetUnderlined(True)

        txt = wx.StaticText(self, label="Locker")
        txt.SetFont(font)
        sizer.Add(txt)
        txt = wx.StaticText(self, label="Status")
        sizer.Add(txt)
        txt.SetFont(font)
        txt = wx.StaticText(self, label="Utilisateur")
        sizer.Add(txt)
        txt.SetFont(font)
        txt = wx.StaticText(self, label="Temps d'utilisation")
        sizer.Add(txt)
        txt.SetFont(font)

        self.staticTexts = {}
        for a_id, desc in ARDUINOS_DESC.items():
            txt_line = []

            txt = wx.StaticText(self, label=desc)
            sizer.Add(txt)
            txt_line.append(txt)
            txt = wx.StaticText(self, label="status")
            sizer.Add(txt)
            txt_line.append(txt)
            txt = wx.StaticText(self, label="user")
            sizer.Add(txt)
            txt_line.append(txt)
            txt = wx.StaticText(self, label="Time")
            sizer.Add(txt)
            txt_line.append(txt)

            self.staticTexts[a_id] = txt_line

        self.SetSizer(sizer)

    def update_infos(self, *event):

        logging.debug("Update de Vue1")

        with LOCK:
            # {'unknown_key', 'key_id',
            #
            # }
            notify = copy.deepcopy(ArduinoCrawler().mainwindow_notify)
            ArduinoCrawler().mainwindow_notify.clear()

        new_key = notify.get("unknown_key", None)
        if new_key is not None:
            resp = wx.MessageBox(
                "On a détecté une clé inconnue. Vous souhaitez l'ajouter ?",
                "Nouvelle clé",
                style=wx.OK | wx.CANCEL,
            )
            if resp == wx.OK:
                self.GetParent().onNewKey(new_key=new_key)

        with LOCK:
            # {'arduino_id': 'unlock_key', ... }
            states = copy.deepcopy(ArduinoCrawler().arduinos_states)

        with DbCursor() as c:
            c.execute("SELECT * FROM keys")
            r_keys = c.fetchall()

        for a_id in self.staticTexts:
            # key_id is None = > Pas d'utilisateur "loggé"
            if states[a_id] is None:
                self.staticTexts[a_id][1].SetLabel("LOCKED")
                self.staticTexts[a_id][2].SetLabel("N/A")
                self.staticTexts[a_id][3].SetLabel(" -- -- -- ")
            else:
                self.staticTexts[a_id][1].SetLabel("UNLOCKED")
                for line in r_keys:
                    if line["key_id"] == states[a_id]:
                        self.staticTexts[a_id][2].SetLabel(
                            line["name"] + " " + line["surname"]
                        )

                with DbCursor() as c:
                    c.execute(
                        "SELECT * FROM stamps WHERE key_id = ? AND arduino_id = ?"
                        " ORDER BY timestamp DESC LIMIT 1",
                        (states[a_id], a_id),
                    )
                    r_stamp = c.fetchone()

                now = datetime.datetime.now()
                starttime = datetime.datetime.strptime(
                    r_stamp["timestamp"], "%Y-%m-%d %H:%M:%S.%f"
                )
                duration = now - starttime
                self.staticTexts[a_id][3].SetLabel(str(duration).split(".")[0])

        # self.GetParent().Fit()

        if self.IsShownOnScreen():
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.update_infos, self.timer)
            self.timer.Start(1000, wx.TIMER_ONE_SHOT)


class Vue2(wx.Panel):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        sizer = wx.BoxSizer(wx.VERTICAL)
        flags = wx.SizerFlags(1).Expand()

        col_flags = (
            wx.dataview.DATAVIEW_COL_RESIZABLE | wx.dataview.DATAVIEW_COL_SORTABLE
        )

        self.searchCtrl = wx.SearchCtrl(self, size=wx.Size(80, 40))
        self.searchCtrl.ShowCancelButton(True)

        sizer.Add(self.searchCtrl, border=15, flag=wx.ALIGN_CENTER_HORIZONTAL | wx.BOTH)

        self.stampTab = dataview.DataViewListCtrl(self)
        self.stampTab.AppendTextColumn("Nom", flags=col_flags)
        self.stampTab.AppendTextColumn("Prénom", flags=col_flags)
        self.stampTab.AppendTextColumn("Machine", flags=col_flags)
        self.stampTab.AppendTextColumn("Début", flags=col_flags)
        self.stampTab.AppendTextColumn("Fin", flags=col_flags)
        self.stampTab.AppendTextColumn("Durée", flags=col_flags)
        self.stampTab.AppendTextColumn("Remarque", flags=col_flags)

        sizer.Add(self.stampTab, flags)

        self.SetSizerAndFit(sizer)

    def update_infos(self):

        self.stampTab.DeleteAllItems()

        with DbCursor() as c:
            c.execute("SELECT key_id,name,surname FROM keys")
            keys = c.fetchall()

        for key in keys:
            for a_id in ARDUINOS_DESC:

                with DbCursor() as c:
                    c.execute(
                        "SELECT * FROM stamps WHERE key_id=? AND arduino_id=? "
                        "ORDER BY timestamp DESC ",
                        (key["key_id"], a_id,),
                    )
                    stamps = c.fetchall()

                new_entry = ["", "", "", "", "", "", ""]

                for stamp in stamps:

                    if (
                        stamp["lock_state"] == "locked"
                        or stamp["lock_state"] == "error"
                    ):
                        new_entry[0] = key["name"]
                        new_entry[1] = key["surname"]
                        new_entry[2] = ARDUINOS_DESC[stamp["arduino_id"]]

                        new_entry[4] = stamp["timestamp"]
                        if stamp["lock_state"] == "error":
                            new_entry[6] = "Inscrit après un crash. Peut être incorrect"

                    elif stamp["lock_state"] == "unlocked" and new_entry != []:
                        new_entry[3] = stamp["timestamp"]
                    else:
                        raise RuntimeError(
                            "Inconsistant DB state. Impossilbe to extract data properly"
                        )

                    if new_entry[3] != "" and new_entry[4] != "" and new_entry[5] == "":
                        starttime = datetime.datetime.strptime(
                            new_entry[3], "%Y-%m-%d %H:%M:%S.%f"
                        )
                        endtime = datetime.datetime.strptime(
                            new_entry[4], "%Y-%m-%d %H:%M:%S.%f"
                        )
                        duration = endtime - starttime
                        new_entry[5] = str(duration).split(".")[0]

                        self.stampTab.AppendItem(new_entry)
                        new_entry = ["", "", "", "", "", "", ""]


class Vue3(wx.Panel):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.logger = wx.ListBox(self, name="Logger")

        sizer.Add(self.logger, border=15, proportion=1, flag=wx.EXPAND | wx.ALL)

        self.Bind(wx.EVT_SCROLL_LINEUP, self.onScrollUp, self)

        self.SetSizer(sizer)

        okm.glob.logger = self

    def log(self, string):
        """ Add a string to the view with time """

        n = self.logger.GetCount()
        self.logger.InsertItems([f"{datetime.datetime.now()} // {string}"], n)
        self.logger.EnsureVisible(n)

    def onScrollUp(self, event):
        print(event)


if __name__ == "__main__":

    app = wx.App()
    frm = MainWindow(None)
    app.MainLoop()
