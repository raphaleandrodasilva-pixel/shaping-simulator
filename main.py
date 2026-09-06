#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Shaping Simulator Pro - v2.0
Integração dos artigos:
- NASA: Computer Simulation of Gear Tooth Manufacturing Processes (1990)
- ETH: Face-gear drive: Simulation of shaping as manufacturing process (2022)

Autor: Desenvolvido com base em pesquisas da NASA e ETH Zurich
"""

import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow
import tkinter as tk

def main():
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()