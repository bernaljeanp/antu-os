#!/usr/bin/env python3
"""Recuperación acotada del Bluetooth 0489:e139 cuando falla la orden WMT de arranque.

No descarga módulos, no toca el wifi y nunca reinicia un controlador que BlueZ ya reconoce.
La recuperación es un intento por arranque; su resultado queda en el diario del sistema.
"""
import pathlib
import os
import re
import signal
import subprocess
import time

USB = pathlib.Path("/sys/bus/usb/devices")
MARCA = pathlib.Path("/run/antu-bluetooth-mt7925")


def leer(ruta):
    try:
        return ruta.read_text().strip()
    except OSError:
        return ""


def correr(orden):
    try:
        r = subprocess.run(orden, capture_output=True, text=True, timeout=5, env={**os.environ, "LC_ALL": "C"})
        return r.stdout if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def dispositivos(raiz=USB):
    return [d for d in raiz.glob("*") if leer(d / "idVendor") == "0489" and leer(d / "idProduct") == "e139"]


def controladores(dispositivo):
    return list(dispositivo.glob("*/bluetooth/hci*"))


def reconocido(dispositivo):
    lista = correr(["bluetoothctl", "list"]).lower()
    for hci in controladores(dispositivo):
        direccion = leer(hci / "address").lower()
        if direccion and direccion != "00:00:00:00:00:00" and direccion in lista:
            return True
    return False


def fallo_wmt(dispositivo):
    # Si el controlador desapareció no se puede atribuir con certeza el aviso: no tocarlo.
    diario = correr(["journalctl", "-b", "-k", "--no-pager", "-o", "cat"])
    return any(re.search(r"Bluetooth: " + re.escape(h.name) + r": (?:Execution of wmt command timed out|Failed to send wmt func ctrl)", diario)
               for h in controladores(dispositivo))


def bloqueado():
    # Un Bluetooth apagado por la persona no es un fallo de arranque.
    salida = correr(["rfkill", "--noheadings", "--output", "TYPE,SOFT,HARD"])
    return any("bluetooth" in l.lower() and "blocked" in l.lower().replace("unblocked", "")
               for l in salida.splitlines())


def recuperar(dispositivo):
    if reconocido(dispositivo) or bloqueado() or not fallo_wmt(dispositivo):
        return False
    # Evita dos intentos al reiniciar el servicio; el nombre no viene del usuario.
    try:
        with MARCA.open("x") as f:
            f.write(dispositivo.name + "\n")
    except FileExistsError:
        return False
    print("Bluetooth MT7925: WMT no respondió; un intento de reconfigurar su dispositivo USB.", flush=True)
    # Solo se desautoriza esta función Bluetooth, nunca su concentrador ni la tarjeta wifi.
    autorizacion = dispositivo / "authorized"
    try:
        autorizacion.write_text("0")
        time.sleep(1)
    finally:
        # Reautorizar incluso si llega una interrupción durante la espera.
        autorizacion.write_text("1")
    return True


def main():
    def detener(*_):
        raise SystemExit(0)  # Ejecuta el finally que reautoriza el dispositivo si se apaga en ese instante.

    signal.signal(signal.SIGTERM, detener)
    for dispositivo in dispositivos():
        # La configuración normal del controlador puede tardar. No competir con su primer intento.
        limite = time.monotonic() + 30
        while time.monotonic() < limite:
            if reconocido(dispositivo) or bloqueado():
                return
            time.sleep(1)
        if recuperar(dispositivo):
            limite = time.monotonic() + 30
            while time.monotonic() < limite:
                if reconocido(dispositivo):
                    print("Bluetooth MT7925: controlador reconocido después de la recuperación.", flush=True)
                    return
                time.sleep(1)
            print("Bluetooth MT7925: sigue sin responder; hace falta revisar el informe de este equipo.", flush=True)


if __name__ == "__main__":
    main()
