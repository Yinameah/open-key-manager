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

import argparse
import logging


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
    print(args)

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

    app = wx.App()

    if args.with_simulator:
        from okm.gui.arduinosimulator import SimulatorWindow
        from okm.backend.arduino_crawler import ArduinoCrawler

        simulatorwindow = SimulatorWindow(None)

        # J'initialize le crawler sur arduinos virtuels ;-)
        # Comme c'est un singleton, il le sera toujours dans mainwindow
        ArduinoCrawler(virtual=True, virtual_arduinos=simulatorwindow.arduinos)

    mainwindow = MainWindow(None)
    app.MainLoop()
