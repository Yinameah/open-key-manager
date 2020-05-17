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

from okm.gui.mainwindow import MainWindow
from okm.backend.arduino_crawler import ArduinoCrawler
from okm.glob import DB_PATH, ARDUINOS_DESC
from okm.utils import DbCursor

import argparse
import logging
import sqlite3
import datetime


def main():
    # Parser des arguments de ligne de commande
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l", "--log", choices=["info", "debug"], help="Increase logging level"
    )
    parser.add_argument(
        "--with_simulator", help="Run an arduino simulator", action="store_true"
    )

    args = parser.parse_args()
    # print(args)

    if args.log == "info":
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s.%(msecs)03d %(levelname)s "
            "[%(module)s/%(funcName)s]: %(message)s",
            datefmt="%H:%M:%S",
        )
    elif args.log == "debug":
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s.%(msecs)03d %(levelname)s [%(module)s/%(funcName)s]: %(message)s",
            datefmt="%H:%M:%S",
        )

    if args.with_simulator:
        from okm.gui.arduinosimulator import SimulatorWindow

        simulatorwindow = SimulatorWindow(None)

    # Verify that we don't have entry in DB that stayed open (from a crash)
    with DbCursor() as c:
        c.execute("SELECT key_id FROM keys")
        r1 = c.fetchall()
        c.execute("SELECT * FROM stamps ORDER BY timestamp DESC ")
        r2 = c.fetchall()

    key_to_check = [l[0] for l in r1]
    key_to_check.sort()
    key_already_checked = []
    for line in r2:
        if line["key_id"] not in key_already_checked:
            key_already_checked.append(line["key_id"])
            if line["lock_state"] == "unlocked":

                print(f"La clé {line['key_id']} est restée ouverte. On y remédie...")

                timestamp = datetime.datetime.now()
                new_data = (line["key_id"], line["arduino_id"], timestamp, "error")

                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("INSERT INTO stamps VALUES (?, ?, ?, ?)", new_data)
                conn.commit()
                conn.close()

        if key_to_check == sorted(key_already_checked):
            break

    app = wx.App(False)
    # Start crawler
    ArduinoCrawler()

    mainwindow = MainWindow(None)
    app.MainLoop()

    # TODO :
    # Close all stamps in DB and close all arduinos when quitting application
