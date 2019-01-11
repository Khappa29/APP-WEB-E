# -*- coding: utf-8 -*-
"""
Éditeur de Spyder

Ceci est un script temporaire.
"""
import sqlite3
database = "base.sqlite"
conn = sqlite3.connect(database)
c = conn.cursor()
c.execute("SELECT STAID FROM 'stations-meteo' WHERE STANAME='NICE'")
r = c.fetchall()
print(r[0])