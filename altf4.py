#!/usr/bin/env python3

import time
import keyboard

# Kleine vertraging zodat EmulationStation volledig is afgesloten
time.sleep(1)

# Simuleer Alt+F4 op de actieve terminal
keyboard.press_and_release("alt+f4")
