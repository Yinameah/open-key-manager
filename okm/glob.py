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

from pathlib import Path
import threading

"""
Global values
"""

# Path of database
DB_PATH = Path(__file__).parent / "db.sqlite3"

# Description des arduinos. C'est pour leur donner un nom dans le gui
# Cette liste doit être cohérente avec la déclaration d'arduinos dans
# okm.backend.arduinos.get_arduinos(), qui réuitile les mêmes ids que ici
# et déclare le type d'appareils en jeu
# /!/ order count for DB
# {'id' : 'description', ... }
ARDUINOS_DESC = {10: "Tour Metal"}  # , 20: "3d printer", 30: "autre"}


# Brute force but might do the trick ...
LOCK = threading.Lock()

# Other brute force approach ...
# Define moc logger object ... Later, this will be shadowed by gui logger
# Because crawler is started before Gui, it needs empty API to work until
# GUI logger is ready
class MocLogger:
    def log(*args):
        pass


logger = MocLogger()
