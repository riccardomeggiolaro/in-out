#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, cairo

import threading
import evdev
import math
import subprocess
import sys
import os


HWDB_PATH = '/etc/udev/hwdb.d/99-penmount-calibration.hwdb'


# ─────────────────────────────────────────────
# AUTO DETECT TOUCH
# ─────────────────────────────────────────────
def find_touch_device():
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        name = dev.name.lower()

        if "penmount" in name or "touch" in name:
            try:
                caps = dev.capabilities()
                if evdev.ecodes.EV_ABS in caps:
                    abs_caps = caps[evdev.ecodes.EV_ABS]
                    codes = [c[0] if isinstance(c, tuple) else c for c in abs_caps]
                    if evdev.ecodes.ABS_X in codes and evdev.ecodes.ABS_Y in codes:
                        print("Touch trovato:", path, dev.name)
                        return path
            except:
                pass

    return None


DEVICE_PATH = find_touch_device()

if not DEVICE_PATH:
    print("❌ Touch device non trovato")
    sys.exit(1)


TARGET_FRACTIONS = [
    (0.10, 0.10),
    (0.90, 0.10),
    (0.90, 0.90),
    (0.10, 0.90),
]

LABELS = ["Alto-Sinistra", "Alto-Destra", "Basso-Destra", "Basso-Sinistra"]


# ─────────────────────────────────────────────
# THREAD TOUCH
# ─────────────────────────────────────────────
class TouchReader(threading.Thread):
    def __init__(self, cb):
        super().__init__(daemon=True)
        self.cb = cb
        self.active = True
        self._armed = False
        self.x = None
        self.y = None

    def arm(self):
        self.x = self.y = None
        self._armed = True

    def run(self):
        try:
            dev = evdev.InputDevice(DEVICE_PATH)

            try:
                dev.grab()
            except Exception as e:
                print("grab warning:", e)

            for event in dev.read_loop():
                if not self.active:
                    break

                if event.type == evdev.ecodes.EV_ABS:
                    if event.code == evdev.ecodes.ABS_X:
                        self.x = event.value
                    elif event.code == evdev.ecodes.ABS_Y:
                        self.y = event.value

                elif event.type == evdev.ecodes.EV_KEY and event.value == 0:
                    if self._armed and self.x is not None:
                        self._armed = False
                        GLib.idle_add(self.cb, self.x, self.y)

        except Exception as e:
            GLib.idle_add(self.cb, -2, -2)
            print("Touch error:", e)

    def stop(self):
        self.active = False


# ─────────────────────────────────────────────
# GUI
# ─────────────────────────────────────────────
class Window(Gtk.Window):

    def __init__(self):
        super().__init__()
        self.set_title("PenMount Calibration")

        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geo = monitor.get_geometry()

        self.w = geo.width
        self.h = geo.height

        self.set_default_size(self.w, self.h)
        self.fullscreen()

        self.area = Gtk.DrawingArea()
        self.area.connect("draw", self.draw)
        self.add(self.area)

        self.idx = 0
        self.points = []

        self.reader = TouchReader(self.on_touch)
        self.reader.start()
        self.reader.arm()

        self.show_all()

    def draw(self, widget, cr):

        cr.set_source_rgb(0.1, 0.1, 0.15)
        cr.paint()

        if self.idx >= len(TARGET_FRACTIONS):
            cr.set_source_rgb(0, 1, 0)
            cr.move_to(self.w/2, self.h/2)
            cr.show_text("DONE")
            return

        fx, fy = TARGET_FRACTIONS[self.idx]
        x = int(fx * self.w)
        y = int(fy * self.h)

        cr.set_source_rgb(1, 0, 0)
        cr.arc(x, y, 20, 0, 6.28)
        cr.stroke()

    def on_touch(self, x, y):

        if x < 0:
            print("error touch")
            return False

        print("touch:", x, y)

        self.points.append((x, y))
        self.idx += 1

        self.area.queue_draw()

        if self.idx < 4:
            GLib.timeout_add(300, self.reader.arm)

        return False


def main():
    if not DEVICE_PATH:
        print("no device")
        return

    win = Window()
    Gtk.main()


if __name__ == "__main__":
    main()