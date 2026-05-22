#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, cairo

import threading
import evdev
import subprocess
import sys
import os


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
                        return path, dev.name
            except:
                pass

    return None, None


DEVICE_PATH, DEVICE_NAME = find_touch_device()

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
# CALCOLO CALIBRAZIONE
# ─────────────────────────────────────────────
def compute_calibration(points):
    x1, y1 = points[0]  # TL
    x2, y2 = points[1]  # TR
    x3, y3 = points[2]  # BR
    x4, y4 = points[3]  # BL

    avg_left   = (x1 + x4) / 2
    avg_right  = (x2 + x3) / 2
    avg_top    = (y1 + y2) / 2
    avg_bottom = (y3 + y4) / 2

    fx_lo = TARGET_FRACTIONS[0][0]   # 0.10
    fx_hi = TARGET_FRACTIONS[1][0]   # 0.90
    fy_lo = TARGET_FRACTIONS[0][1]   # 0.10
    fy_hi = TARGET_FRACTIONS[2][1]   # 0.90

    x_range = (avg_right - avg_left) / (fx_hi - fx_lo)
    min_x = int(round(avg_left - fx_lo * x_range))
    max_x = int(round(min_x + x_range))

    y_range = (avg_bottom - avg_top) / (fy_hi - fy_lo)
    min_y = int(round(avg_top - fy_lo * y_range))
    max_y = int(round(min_y + y_range))

    return min_x, max_x, min_y, max_y


# ─────────────────────────────────────────────
# APPLICA VIA XINPUT
# ─────────────────────────────────────────────
def apply_xinput(min_x, max_x, min_y, max_y, device_name):
    try:
        result = subprocess.run(
            ['xinput', 'set-prop', device_name,
             'Evdev Axis Calibration',
             str(min_x), str(max_x), str(min_y), str(max_y)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("[OK] Calibrazione applicata via xinput")
        else:
            print(f"[WARN] xinput: {result.stderr.strip()}")
    except FileNotFoundError:
        print("[WARN] xinput non trovato, solo xorg.conf.d sarà aggiornato")


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
        self.set_title("PenMount Calibration - XOrg")

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
            cr.set_font_size(64)
            cr.move_to(self.w / 2 - 80, self.h / 2)
            cr.show_text("DONE")
            return

        fx, fy = TARGET_FRACTIONS[self.idx]
        x = int(fx * self.w)
        y = int(fy * self.h)

        cr.set_source_rgb(1, 0, 0)
        cr.arc(x, y, 20, 0, 6.28)
        cr.stroke()

        cr.set_source_rgb(1, 1, 1)
        cr.set_font_size(24)
        label = LABELS[self.idx]
        cr.move_to(self.w / 2 - 100, self.h / 2)
        cr.show_text(f"Tocca: {label}  ({self.idx + 1}/4)")

    def on_touch(self, x, y):

        if x < 0:
            print("error touch")
            return False

        label = LABELS[self.idx] if self.idx < 4 else "?"
        print(f"touch {label}: {x}, {y}")

        self.points.append((x, y))
        self.idx += 1

        self.area.queue_draw()

        if self.idx == 4:
            GLib.timeout_add(500, self.finalize)
        elif self.idx < 4:
            GLib.timeout_add(300, self.reader.arm)

        return False

    def finalize(self):
        min_x, max_x, min_y, max_y = compute_calibration(self.points)

        print(f"CALIB: {min_x} {max_x} {min_y} {max_y}")

        apply_xinput(min_x, max_x, min_y, max_y, DEVICE_NAME)

        GLib.timeout_add(1500, Gtk.main_quit)
        return False


def main():
    win = Window()
    Gtk.main()


if __name__ == "__main__":
    main()
