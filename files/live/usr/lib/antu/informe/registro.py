#!/usr/bin/env python3
"""Registro del USB en vivo: muestras cada cinco segundos y un avance guardado cada minuto.

Solo lee sensores y estado del sistema. No inspecciona archivos personales ni carga código en juegos.
El servicio sigue activo al cerrar la ventana del informe. La GPU dormida no se despierta para medirla.
"""
import datetime
import json
import os
import pathlib
import runpy
import signal
import socket
import subprocess
import threading
import time

CARPETA = pathlib.Path("/run/antu-informe")
CADA = 5
MAX_MUESTRAS = 4 * 3600 // CADA
CONSULTA_GPU = ["nvidia-smi", "--format=csv,noheader,nounits",
                "--query-gpu=temperature.gpu,utilization.gpu,power.draw,clocks.gr,memory.used,pstate"]


def leer(ruta, defecto=""):
    try:
        return pathlib.Path(ruta).read_text().strip()
    except OSError:
        return defecto


def atomico(ruta, texto):
    temporal = ruta.with_name(ruta.name + ".tmp")
    with temporal.open("w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    temporal.replace(ruta)


def nvidia_despierta(raiz=pathlib.Path("/sys/bus/pci/devices")):
    return any(leer(d / "vendor") == "0x10de" and leer(d / "class").startswith("0x03")
               and leer(d / "power/runtime_status") == "active" for d in raiz.glob("*"))


def correr(orden, limite=3):
    try:
        r = subprocess.run(orden, capture_output=True, text=True, timeout=limite)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def zenit():
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect("/run/zenit.sock")
            s.sendall(b'["estado"]\n')
            datos = json.loads(s.makefile().readline(65536))
        return {k: datos.get(k) for k in ("perfil", "temperaturas", "ventiladores", "boost", "juego")}
    except (OSError, ValueError):
        return {"temperaturas": {}, "ventiladores": {}, "error": "Zenit sin respuesta"}


def cpu(raiz=pathlib.Path("/proc")):
    try:
        numeros = [int(n) for n in leer(raiz / "stat").splitlines()[0].split()[1:9]]
        return sum(numeros), numeros[3] + numeros[4]
    except (ValueError, IndexError):
        return None


def estrangulamientos(raiz=pathlib.Path("/sys/devices/system/cpu")):
    # Contadores reales del núcleo, sin deducir sobrecalentamiento a partir de una sola temperatura.
    datos = {}
    for ruta in raiz.glob("cpu[0-9]*/thermal_throttle/*_throttle_count"):
        valor = leer(ruta)
        if valor.isdigit():
            datos[ruta.parent.parent.name + "/" + ruta.name] = int(valor)
    return datos


def muestra(anterior=None):
    actual = cpu()
    uso = None
    if anterior and actual and actual[0] > anterior[0]:
        uso = round(100 * (1 - (actual[1] - anterior[1]) / (actual[0] - anterior[0])), 1)
    grafica = correr(CONSULTA_GPU) if nvidia_despierta() else "dormida o no disponible; no se despierta para medir"
    return {"hora": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "segundo": round(time.monotonic(), 2), "cpu_uso": uso,
            "carga": leer("/proc/loadavg").split()[:3], "grafica": grafica,
            "zenit": zenit(), "limites_termicos": estrangulamientos()}, actual


def mediciones(carpeta=CARPETA):
    salida = []
    try:
        with (carpeta / "mediciones.jsonl").open(encoding="utf-8") as f:
            for linea in f:
                try:
                    salida.append(json.loads(linea))
                except ValueError:
                    pass  # Una última línea aún en escritura no invalida las anteriores.
                if len(salida) == MAX_MUESTRAS:
                    break
    except OSError:
        pass
    return salida


def resumen(datos):
    if not datos:
        return "Sin muestras. No se pueden evaluar temperaturas sostenidas ni rendimiento."
    segundos = max(0, datos[-1]["segundo"] - datos[0]["segundo"])
    temperaturas = [d["zenit"].get("temperaturas", {}).get("CPU") for d in datos]
    temperaturas = [n for n in temperaturas if isinstance(n, (int, float))]
    partes = [f"Muestras: {len(datos)}. Período entre primera y última: {segundos:.0f} s.",
              "Las pausas no se miden. No es una prueba de fotogramas ni de estabilidad de un juego."]
    if temperaturas:
        partes.append(f"CPU: mínima {min(temperaturas)} °C, máxima {max(temperaturas)} °C.")
    if len(datos) < 12 or segundos < 60:
        partes.append("Registro breve: no permite saber si una temperatura alta se mantuvo.")
    incrementos = []
    primero, ultimo = datos[0].get("limites_termicos", {}), datos[-1].get("limites_termicos", {})
    for clave in primero.keys() & ultimo.keys():
        if ultimo[clave] > primero[clave]:
            incrementos.append(f"{clave}: +{ultimo[clave] - primero[clave]}")
    detalle = ", ".join(sorted(incrementos)) or "sin incrementos observados."
    if not primero.keys() & ultimo.keys():
        detalle = "no disponibles; no se puede evaluar la limitación térmica con ellos."
    partes.append("Contadores de limitación térmica: " + detalle)
    return "\n".join(partes)


def texto_registro(carpeta=CARPETA):
    datos = mediciones(carpeta)
    return ("\n\n===== Registro mientras se probaba =====\n" + resumen(datos)
            + "\nGráfica: °C, uso %, W, MHz, memoria MiB, estado.\n"
            + "\n".join(json.dumps(d, ensure_ascii=False) for d in datos))


def guardar_avance(helper, nombre, carpeta=CARPETA):
    # La captura privilegiada no entra en el hilo de muestreo: crear el informe no deja huecos en las mediciones.
    sesion = correr(["systemd-run", "--user", "--machine=antu@", "--wait", "--pipe", "--quiet",
                     "/usr/bin/python3", "/usr/lib/antu/informe/informe.py", "--sesion-rapida"], limite=5)
    contenido = helper["armar"](sesion, limite=15).encode()
    nombre_local = carpeta / "avance.txt"
    atomico(nombre_local, contenido.decode())
    return helper["en_el_usb"](nombre, contenido)


def ejecutar(carpeta=CARPETA):
    import fcntl
    helper = runpy.run_path(str(pathlib.Path(__file__).resolve().parent.parent / "informe-helper"))
    carpeta.mkdir(parents=True, exist_ok=True)
    # Una sola instancia, incluso cuando la persona abre el informe mientras arranca el servicio.
    with (carpeta / "registro.lock").open("w") as cerrojo:
        fcntl.flock(cerrojo, fcntl.LOCK_EX | fcntl.LOCK_NB)
        datos = mediciones(carpeta)
        estado_previo = {}
        try:
            estado_previo = json.loads(leer(carpeta / "estado.json", "{}"))
        except ValueError:
            pass
        if len(datos) >= MAX_MUESTRAS:
            datos = []
            (carpeta / "mediciones.jsonl").unlink(missing_ok=True)
            estado_previo = {}
        # Después de una interrupción puede quedar media línea: no concatenar la muestra nueva con esa línea.
        atomico(carpeta / "mediciones.jsonl", "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in datos))
        nombre = estado_previo.get("archivo") or time.strftime("informe-live-%Y%m%d-%H%M%S.txt")
        parar = threading.Event()
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda *_: parar.set())
        exportacion = None
        guardado = {"usb": False, "error": "", "ultimo_guardado": ""}
        siguiente = time.monotonic()
        anterior = None

        def exportar():
            try:
                guardado["usb"] = guardar_avance(helper, nombre, carpeta)
                guardado["error"] = "" if guardado["usb"] else "No se pudo guardar este avance en el USB."
                if guardado["usb"]:
                    guardado["ultimo_guardado"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
            except Exception as e:
                guardado["usb"] = False
                guardado["error"] = str(e)

        def estado(activo):
            segundos = max(0, datos[-1]["segundo"] - datos[0]["segundo"]) if datos else 0
            atomico(carpeta / "estado.json", json.dumps({"activo": activo, "muestras": len(datos),
                    "segundos": segundos, "archivo": nombre, **guardado}, ensure_ascii=False))

        try:
            with (carpeta / "mediciones.jsonl").open("a", encoding="utf-8", newline="\n") as archivo:
                while not parar.is_set() and len(datos) < MAX_MUESTRAS:
                    inicio = time.monotonic()
                    dato, anterior = muestra(anterior)
                    archivo.write(json.dumps(dato, ensure_ascii=False) + "\n")
                    archivo.flush()
                    datos.append(dato)
                    if inicio >= siguiente and (exportacion is None or not exportacion.is_alive()):
                        exportacion = threading.Thread(target=exportar, daemon=True)
                        exportacion.start()
                        siguiente = inicio + 60
                    estado(True)
                    parar.wait(max(0, CADA - (time.monotonic() - inicio)))
        finally:
            if exportacion:
                exportacion.join(timeout=35)
            if exportacion is None or not exportacion.is_alive():
                # En la salida basta con actualizar las muestras; no volver a consultar todos los servicios al apagar.
                avance = leer(carpeta / "avance.txt")
                if avance:
                    cabecera = avance.split("\n\n===== Registro mientras se probaba =====", 1)[0]
                    try:
                        guardado["usb"] = helper["en_el_usb"](nombre, helper["limpiar"](cabecera + texto_registro(carpeta)).encode())
                        guardado["error"] = "" if guardado["usb"] else "No se pudo guardar el último avance en el USB."
                        if guardado["usb"]:
                            guardado["ultimo_guardado"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
                    except OSError as e:
                        guardado["usb"], guardado["error"] = False, str(e)
            estado(False)


if __name__ == "__main__":
    ejecutar()
