#!/usr/bin/env python3
"""
Taratura Touch IEI PenMount - Wayland/libinput
Mostra 4 punti, legge tocchi raw da evdev, scrive matrice in udev hwdb.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import threading
import evdev
import math
import subprocess
import sys
import os

DEVICE_PATH = '/dev/input/event0'
HWDB_PATH   = '/etc/udev/hwdb.d/99-penmount-calibration.hwdb'

# Posizioni dei 4 punti di taratura (frazione dello schermo)
TARGET_FRACTIONS = [
    (0.10, 0.10),   # 1 - alto-sinistra
    (0.90, 0.10),   # 2 - alto-destra
    (0.90, 0.90),   # 3 - basso-destra
    (0.10, 0.90),   # 4 - basso-sinistra
]
LABELS = ["Alto-Sinistra", "Alto-Destra", "Basso-Destra", "Basso-Sinistra"]


# ─────────────────────────────────────────────
# Thread lettore eventi evdev
# ─────────────────────────────────────────────
class TouchReader(threading.Thread):
    def __init__(self, on_touch_cb):
        super().__init__(daemon=True)
        self.on_touch_cb = on_touch_cb  # chiamata con (raw_x, raw_y) nel thread GTK
        self.active = True
        self._armed = False             # True = aspetta il prossimo tocco
        self._cur_x = self._cur_y = None

    def arm(self):
        """Abilita la cattura del prossimo tocco."""
        self._cur_x = self._cur_y = None
        self._armed = True

    def run(self):
        try:
            dev = evdev.InputDevice(DEVICE_PATH)
            dev.grab()
            for event in dev.read_loop():
                if not self.active:
                    break
                if event.type == evdev.ecodes.EV_ABS:
                    if event.code == evdev.ecodes.ABS_X:
                        self._cur_x = event.value
                    elif event.code == evdev.ecodes.ABS_Y:
                        self._cur_y = event.value
                elif (event.type == evdev.ecodes.EV_KEY
                      and event.code == evdev.ecodes.BTN_TOUCH
                      and event.value == 0):          # dito alzato
                    if self._armed and self._cur_x is not None:
                        self._armed = False
                        GLib.idle_add(self.on_touch_cb, self._cur_x, self._cur_y)
            try:
                dev.ungrab()
                dev.close()
            except Exception:
                pass
        except PermissionError:
            GLib.idle_add(self.on_touch_cb, -1, -1)
        except Exception as e:
            print(f"[TouchReader] Errore: {e}", file=sys.stderr)
            GLib.idle_add(self.on_touch_cb, -2, -2)

    def stop(self):
        self.active = False


# ─────────────────────────────────────────────
# Finestra di calibrazione
# ─────────────────────────────────────────────
class CalibrationWindow(Gtk.Window):

    def __init__(self):
        super().__init__()
        self.set_title("Taratura Touch IEI PenMount")

        # Dimensioni monitor primario (fallback a 1024x768)
        self.sw = 1024
        self.sh = 768
        try:
            display = Gdk.Display.get_default()
            if display:
                monitor = display.get_primary_monitor()
                if monitor:
                    geom = monitor.get_geometry()
                    self.sw = geom.width
                    self.sh = geom.height
        except Exception as e:
            print(f"[WARN] Monitor detection fallback a {self.sw}x{self.sh}: {e}")
        print(f"[Display] {self.sw}x{self.sh}")

        self.set_default_size(self.sw, self.sh)
        self.fullscreen()
        self.set_keep_above(True)

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect('draw', self._on_draw)
        self.add(self.drawing_area)

        self.current_pt  = 0
        self.raw_points  = []
        self.done        = False
        self.error_msg   = None
        self.final_msg   = ""

        # Leggi range assi dal device
        self.raw_xmin = self.raw_xmax = None
        self.raw_ymin = self.raw_ymax = None
        self._read_device_range()

        # Avvia lettore touch
        self.reader = TouchReader(self._on_touch)
        self.reader.start()
        self.reader.arm()

        self.show_all()
        self.connect('destroy', self._on_destroy)

    # ── Range assi ──
    def _read_device_range(self):
        try:
            dev = evdev.InputDevice(DEVICE_PATH)
            xi = dev.absinfo(evdev.ecodes.ABS_X)
            yi = dev.absinfo(evdev.ecodes.ABS_Y)
            self.raw_xmin, self.raw_xmax = xi.min, xi.max
            self.raw_ymin, self.raw_ymax = yi.min, yi.max
            dev.close()
            print(f"[Device] {DEVICE_PATH}  ABS_X:[{xi.min},{xi.max}]  ABS_Y:[{yi.min},{yi.max}]")
        except Exception as e:
            self.error_msg = f"Errore apertura device: {e}"

    # ── Disegno ──
    def _on_draw(self, _widget, cr):
        w = self.drawing_area.get_allocated_width()
        h = self.drawing_area.get_allocated_height()

        # Sfondo scuro
        cr.set_source_rgb(0.08, 0.08, 0.14)
        cr.paint()

        if self.error_msg:
            self._draw_centered_text(cr, w, h, self.error_msg, 22, (1, 0.3, 0.3))
            return

        if self.done:
            self._draw_centered_text(cr, w, h, "✓ Taratura completata!", 30, (0.3, 1, 0.4))
            self._draw_centered_text(cr, w, h + 60, self.final_msg, 18, (0.7, 0.7, 0.7))
            return

        if self.current_pt < len(TARGET_FRACTIONS):
            fx, fy   = TARGET_FRACTIONS[self.current_pt]
            tx, ty   = int(fx * w), int(fy * h)
            arm_size = 32

            # Mirino rosso
            cr.set_source_rgb(1, 0.15, 0.15)
            cr.set_line_width(2.5)
            cr.move_to(tx - arm_size, ty); cr.line_to(tx + arm_size, ty); cr.stroke()
            cr.move_to(tx, ty - arm_size); cr.line_to(tx, ty + arm_size); cr.stroke()
            cr.arc(tx, ty, 14, 0, 2 * math.pi); cr.stroke()
            cr.set_source_rgb(1, 1, 1)
            cr.arc(tx, ty, 3, 0, 2 * math.pi); cr.fill()

            # Testo centrale
            label = f"Punto {self.current_pt + 1}/4  —  {LABELS[self.current_pt]}"
            self._draw_centered_text(cr, w, h, label, 26, (0.9, 0.9, 0.9))
            self._draw_centered_text(cr, w, h + 45, "Tocca il centro del mirino rosso", 18, (0.55, 0.55, 0.65))

            # Indicatori progresso
            for i in range(4):
                cx = w // 2 - 45 + i * 30
                cy = h // 2 + 85
                if i < self.current_pt:
                    cr.set_source_rgb(0.25, 0.65, 1.0)
                elif i == self.current_pt:
                    cr.set_source_rgb(1, 0.4, 0.4)
                else:
                    cr.set_source_rgb(0.25, 0.25, 0.35)
                cr.arc(cx, cy, 9, 0, 2 * math.pi)
                cr.fill()

    def _draw_centered_text(self, cr, w, h, text, size, color):
        cr.set_font_size(size)
        cr.set_source_rgb(*color)
        ext = cr.text_extents(text)
        cr.move_to(w / 2 - ext.width / 2, h / 2 + ext.height / 2)
        cr.show_text(text)

    # ── Callback tocco (GTK main thread) ──
    def _on_touch(self, raw_x, raw_y):
        if raw_x == -1:
            self.error_msg = (f"Permesso negato su {DEVICE_PATH}.\n"
                              "Aggiungi l'utente al gruppo 'input':\n"
                              "  sudo usermod -aG input $USER  (poi riloggati)")
            self.drawing_area.queue_draw()
            return False
        if raw_x == -2:
            self.error_msg = "Errore lettura device. Controlla i log."
            self.drawing_area.queue_draw()
            return False

        print(f"  Punto {self.current_pt + 1} ({LABELS[self.current_pt]}): raw=({raw_x}, {raw_y})")
        self.raw_points.append((raw_x, raw_y))
        self.current_pt += 1
        self.drawing_area.queue_draw()

        if self.current_pt < len(TARGET_FRACTIONS):
            # Debounce 400ms, poi arma per il prossimo punto
            GLib.timeout_add(400, self._arm_reader)
        else:
            GLib.timeout_add(300, self._calculate)
        return False

    def _arm_reader(self):
        self.reader.arm()
        return False

    # ── Calcolo matrice ──
    def _calculate(self):
        print("\n--- Calcolo matrice di calibrazione ---")

        xmin, xmax = self.raw_xmin, self.raw_xmax
        ymin, ymax = self.raw_ymin, self.raw_ymax

        # Normalizza i punti raw in [0, 1]
        rn = [((x - xmin) / (xmax - xmin),
               (y - ymin) / (ymax - ymin))
              for x, y in self.raw_points]

        for i, (rx, ry) in enumerate(rn):
            tx, ty = TARGET_FRACTIONS[i]
            print(f"  {LABELS[i]}: norm=({rx:.4f},{ry:.4f})  target=({tx:.4f},{ty:.4f})")

        # Media X lato sinistro (punti 0 e 3) e destro (1 e 2)
        raw_lx = (rn[0][0] + rn[3][0]) / 2
        raw_rx = (rn[1][0] + rn[2][0]) / 2
        # Media Y lato alto (0 e 1) e basso (2 e 3)
        raw_ty = (rn[0][1] + rn[1][1]) / 2
        raw_by = (rn[2][1] + rn[3][1]) / 2

        tgt_lx = (TARGET_FRACTIONS[0][0] + TARGET_FRACTIONS[3][0]) / 2   # 0.10
        tgt_rx = (TARGET_FRACTIONS[1][0] + TARGET_FRACTIONS[2][0]) / 2   # 0.90
        tgt_ty = (TARGET_FRACTIONS[0][1] + TARGET_FRACTIONS[1][1]) / 2   # 0.10
        tgt_by = (TARGET_FRACTIONS[2][1] + TARGET_FRACTIONS[3][1]) / 2   # 0.90

        a = (tgt_rx - tgt_lx) / (raw_rx - raw_lx)
        c = tgt_lx - a * raw_lx
        e = (tgt_by - tgt_ty) / (raw_by - raw_ty)
        f = tgt_ty - e * raw_ty
        b = d = 0.0

        matrix = f"{a:.6f} {b:.6f} {c:.6f} {d:.6f} {e:.6f} {f:.6f}"
        print(f"\nMatrice: {matrix}")

        vid, pid = self._get_vid_pid()
        if vid and pid:
            self._write_hwdb(vid, pid, matrix)
        else:
            self.final_msg  = f"Matrice: {matrix}  (hwdb non scritto: VID/PID non rilevati)"
            self.done       = True
            self.drawing_area.queue_draw()
        return False

    def _get_vid_pid(self):
        try:
            out = subprocess.run(
                ['udevadm', 'info', '--query=property', DEVICE_PATH],
                capture_output=True, text=True
            ).stdout
            vid = pid = None
            for line in out.splitlines():
                if line.startswith('ID_VENDOR_ID='):
                    vid = line.split('=', 1)[1].strip().upper().zfill(4)
                elif line.startswith('ID_MODEL_ID='):
                    pid = line.split('=', 1)[1].strip().upper().zfill(4)
            print(f"  VID={vid}  PID={pid}")
            return vid, pid
        except Exception as e:
            print(f"[get_vid_pid] {e}", file=sys.stderr)
            return None, None

    def _write_hwdb(self, vid, pid, matrix):
        content = (
            "# Taratura PenMount IEI - generata da calibrate_penmount_gui.py\n"
            f"evdev:input:b0003v{vid}p{pid}*\n"
            f" LIBINPUT_CALIBRATION_MATRIX={matrix}\n"
        )
        print(f"\nContenuto hwdb:\n{content}")
        try:
            # Backup del file esistente
            if os.path.exists(HWDB_PATH):
                subprocess.run(['sudo', 'cp', HWDB_PATH, HWDB_PATH + '.bak'], check=True)
                print(f"  Backup: {HWDB_PATH}.bak")

            # Scrivi hwdb
            r = subprocess.run(['sudo', 'tee', HWDB_PATH],
                               input=content, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(r.stderr.strip())

            # Aggiorna e notifica udev
            subprocess.run(['sudo', 'systemd-hwdb', 'update'], check=True)
            subprocess.run(['sudo', 'udevadm', 'trigger',
                            '--subsystem-match=input', '--action=change'], check=True)

            print(f"  hwdb scritto: {HWDB_PATH}")
            self.final_msg = "Scollega e ricollega il touch USB per applicare"
            self.done = True
            self.drawing_area.queue_draw()
            GLib.timeout_add(4000, lambda: (Gtk.main_quit(), False)[1])

        except Exception as e:
            self.error_msg = f"Errore scrittura hwdb: {e}"
            self.drawing_area.queue_draw()

    def _on_destroy(self, _w):
        self.reader.stop()
        Gtk.main_quit()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    # Controllo dipendenze
    try:
        import evdev  # noqa: F401
    except ImportError:
        print("Errore: python3-evdev non installato.\n  sudo apt install python3-evdev", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(DEVICE_PATH):
        print(f"Errore: {DEVICE_PATH} non trovato. Touch connesso?", file=sys.stderr)
        sys.exit(1)

    if not os.access(DEVICE_PATH, os.R_OK):
        print(f"Errore: permesso negato su {DEVICE_PATH}.\n"
              "  sudo usermod -aG input $USER  (poi riloggati)", file=sys.stderr)
        sys.exit(1)

    # Auto-rileva display se non impostato
    uid = os.getuid()
    if not os.environ.get('WAYLAND_DISPLAY'):
        for name in ['wayland-0', 'wayland-1']:
            sock = f'/run/user/{uid}/{name}'
            if os.path.exists(sock):
                os.environ['WAYLAND_DISPLAY'] = name
                print(f"[INFO] WAYLAND_DISPLAY={name} (auto-rilevato)")
                break
    if not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
        os.environ['DISPLAY'] = ':0'
        print("[INFO] Nessun display rilevato, provo DISPLAY=:0")

    # XDG_RUNTIME_DIR necessario per Wayland
    xdg = os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{uid}')
    os.environ.setdefault('XDG_RUNTIME_DIR', xdg)

    win = CalibrationWindow()  # noqa: F841
    Gtk.main()


if __name__ == '__main__':
    main()