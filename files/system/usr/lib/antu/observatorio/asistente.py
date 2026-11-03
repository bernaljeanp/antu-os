#!/usr/bin/env python3
"""Asistente del Observatorio: responde sobre un juego con tus mediciones, en tu propia gráfica y sin internet.

Usa Ollama, que viene en el sistema, y un modelo que se baja una sola vez cuando la persona lo activa. El motor se abre solo al
preguntar y se cierra con la ventana: mientras juegas no ocupa nada. Solo responde: no ejecuta nada en el equipo. Nada sale de aquí.

--autoprueba: revisa lo que se le entrega al modelo.
--real: baja el modelo y le hace preguntas de verdad (ci/asistente.sh).
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request

MODELO = "qwen3.5:4b"
BYTES_DEL_MODELO = 3.4e9
PUERTO = 11435
URL = f"http://127.0.0.1:{PUERTO}"
CARPETA = pathlib.Path.home() / ".local/share/antu/asistente"
SESIONES_EN_CONTEXTO = 12

SISTEMA = """Eres el asistente de Antu OS, un sistema para jugar. Respondes sobre el rendimiento de un juego usando solo las mediciones que te entregan.

Reglas:
- Responde en español, en un máximo de cinco frases cortas y en texto simple, sin listas ni formato.
- Usa los números de las mediciones. Nunca inventes un número, una causa segura ni un dato que no esté en ellas.
- Si las mediciones no alcanzan para responder, dilo y explica qué faltaría medir.
- Di «lo más probable» cuando sea una deducción. Coincidir en la fecha no demuestra la causa.
- Nunca pidas abrir una terminal ni escribir comandos. Todo se hace desde las ventanas de Antu.

Qué puede hacer la persona:
- Si el juego rinde menos desde una actualización: en el Observatorio, el botón «Volver atrás» deja la versión anterior para el próximo reinicio. También pudo cambiar un ajuste del juego.
- Si la gráfica se calentó y bajó potencia: despejar las rejillas de ventilación, usar una base con ventilador y elegir el perfil Rendimiento en Zenit.
- Si jugó con batería: conectar el cargador, porque con batería el equipo rinde menos.
- Si no hay fotogramas medidos: se miden al jugar en el modo Eclipse.
- Si el juego se cerró por falta de memoria: cerrar otras aplicaciones, como el navegador, antes de jugar.
- Si un juego no abre o no deja entrar a partidas en línea: la Biblioteca dice si funciona y si su antitrampas lo permite."""


def contexto(juego):
    """Las mediciones de un juego (lo que arma observatorio.resumir), en palabras para el modelo."""
    lineas = [f"Juego: {juego['nombre']}", f"Estado: {juego['titulo']}"]
    if juego.get("detalle"):
        lineas.append(f"Detalle: {juego['detalle']}")
    if juego.get("cambios"):
        lineas.append("Qué cambió en el sistema: " + "; ".join(juego["cambios"].split("\n")))
    if juego.get("notas"):
        lineas.append("Última sesión: " + " ".join(juego["notas"].split("\n")))
    sesiones = []
    for s in juego.get("sesiones", [])[-SESIONES_EN_CONTEXTO:]:
        fps = f"{s['fps']:.0f} fotogramas por segundo" if s.get("fps") else "fotogramas sin medir"
        peores = f", peores momentos {s['bajo']:.0f}" if s.get("bajo") else ""
        temp = f", gráfica a {s['temp']:.0f} °C" if s.get("temp") else ""
        sesiones.append(f"- {s['fecha']}: {fps}{peores}{temp}, {s['minutos']} minutos, con {s['energia'].lower()}")
    if sesiones:
        lineas.append("Sesiones, de la más antigua a la última:\n" + "\n".join(sesiones))
    return "\n".join(lineas)


def limpiar(texto):
    """Sin el razonamiento interno, si el modelo lo escribe."""
    return re.sub(r"<think>.*?(</think>|$)", "", texto, flags=re.S).strip()


def modelo_listo(carpeta=CARPETA):
    nombre, etiqueta = MODELO.split(":")
    return (carpeta / "manifests/registry.ollama.ai/library" / nombre / etiqueta).is_file()


def hay_espacio(carpeta=CARPETA):
    carpeta.mkdir(parents=True, exist_ok=True)
    return shutil.disk_usage(carpeta).free > 1.5 * BYTES_DEL_MODELO


def _enviar(ruta, datos, tiempo=None):
    pedido = urllib.request.Request(URL + ruta, data=json.dumps(datos).encode(), headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(pedido, timeout=tiempo)


class Motor:
    """Ollama en esta sesión: solo escucha en este equipo y se cierra con la ventana."""

    def __init__(self):
        self.proceso = None

    def responde(self):
        try:
            with urllib.request.urlopen(URL + "/api/version", timeout=2):
                return True
        except OSError:
            return False

    def abrir(self):
        if self.responde():
            return
        CARPETA.mkdir(parents=True, exist_ok=True)
        entorno = {**os.environ, "OLLAMA_HOST": f"127.0.0.1:{PUERTO}", "OLLAMA_MODELS": str(CARPETA), "OLLAMA_VULKAN": "1"}
        self.proceso = subprocess.Popen(["ollama", "serve"], env=entorno, stdin=subprocess.DEVNULL,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            if self.responde():
                return
            time.sleep(0.5)
        raise OSError("El asistente no pudo abrirse.")

    def cerrar(self):
        if self.proceso:
            self.proceso.terminate()
            self.proceso = None

    def bajar(self, avance):
        """Baja el modelo; si se corta, sigue desde donde iba. avance(fracción)."""
        self.abrir()
        with _enviar("/api/pull", {"model": MODELO, "stream": True}) as r:
            for linea in r:
                dato = json.loads(linea)
                if dato.get("error"):
                    raise OSError(dato["error"])
                if dato.get("total"):
                    avance(dato.get("completed", 0) / dato["total"])

    def preguntar(self, mensajes, trozo):
        """Va entregando la respuesta a medida que se escribe. trozo(texto hasta ahora)."""
        self.abrir()
        escrito = ""
        datos = {"model": MODELO, "messages": mensajes, "stream": True, "think": False,
                 "options": {"temperature": 0.2, "num_ctx": 4096}}
        with _enviar("/api/chat", datos) as r:
            for linea in r:
                dato = json.loads(linea)
                if dato.get("error"):
                    raise OSError(dato["error"])
                escrito += dato.get("message", {}).get("content", "")
                trozo(limpiar(escrito))
        return limpiar(escrito)


def mensajes_para(juego, historia, pregunta):
    """Instrucciones, mediciones, lo ya conversado y la pregunta."""
    return [{"role": "system", "content": SISTEMA + "\n\nMediciones:\n" + contexto(juego)},
            *historia, {"role": "user", "content": pregunta}]


def autoprueba():
    juego = {"nombre": "ELDEN RING", "titulo": "Rinde 12 % menos", "detalle": "De 66 a 58.", "cambios": "NVIDIA: 1 → 2\nNúcleo: 3 → 4",
             "notas": "Bajó a 41.\nLlegó a 81 °C.",
             "sesiones": [{"fecha": f"{d} oct", "fps": 60, "bajo": 40, "temp": 80, "minutos": 45, "energia": "Cargador"} for d in range(1, 21)]}
    c = contexto(juego)
    assert "NVIDIA: 1 → 2; Núcleo: 3 → 4" in c and "Bajó a 41. Llegó a 81 °C." in c
    assert "20 oct" in c and "- 1 oct:" not in c  # solo las últimas
    assert "con cargador" in c
    sin_fps = {"nombre": "J", "titulo": "T", "sesiones": [{"fecha": "1 oct", "fps": 0, "bajo": 0, "temp": 0, "minutos": 1, "energia": "Batería"}]}
    assert "fotogramas sin medir" in contexto(sin_fps) and "peores" not in contexto(sin_fps)
    assert limpiar("<think>hmm</think> Hola") == "Hola" and limpiar("<think>a medias") == ""
    assert mensajes_para(juego, [{"role": "assistant", "content": "a"}], "¿por qué?")[-1]["content"] == "¿por qué?"
    assert modelo_listo(pathlib.Path("/no/existe")) is False
    print("Asistente: lo que recibe el modelo está correcto")


def real():
    """Preguntas de verdad con mediciones inventadas. Falla si no usa los datos o si manda a la terminal."""
    from observatorio import demo, resumir_todo

    juegos = {j["nombre"]: j for j in resumir_todo(demo())}
    motor = Motor()
    try:
        motor.bajar(lambda f: None)
        fallas = 0
        for nombre, pregunta, debe in (
            ("ELDEN RING", "¿Por qué me va más lento?", ("58", "NVIDIA")),
            ("ELDEN RING", "¿Se está calentando demasiado?", ("81",)),
            ("Cyberpunk 2077", "¿Por qué se cerró?", ("memoria",)),
            ("Cyberpunk 2077", "¿A cuántos fotogramas corre?", ("medi",)),
        ):
            inicio = time.time()
            respuesta = motor.preguntar(mensajes_para(juegos[nombre], [], pregunta), lambda t: None)
            print(f"\n[{nombre}] {pregunta} ({time.time() - inicio:.0f} s)\n{respuesta}", flush=True)
            if not all(p.lower() in respuesta.lower() for p in debe) or "terminal" in respuesta.lower():
                print(f"::error::El asistente no respondió con los datos: esperaba {debe}")
                fallas += 1
        sys.exit(1 if fallas else 0)
    finally:
        motor.cerrar()


if __name__ == "__main__":
    if "--real" in sys.argv:
        real()
    else:
        autoprueba()
