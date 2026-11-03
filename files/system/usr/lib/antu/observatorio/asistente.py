#!/usr/bin/env python3
"""Asistente del Observatorio: responde sobre un juego con tus mediciones, en tu propia gráfica y sin internet.

Las conclusiones las calcula Antu y el modelo solo las explica: probado con preguntas reales, un modelo pequeño que deduce por su
cuenta culpa al calor aunque la temperatura no haya cambiado. Usa Ollama, que viene en el sistema, y un modelo que se baja una sola vez cuando la persona lo activa. El motor se abre solo al
preguntar y se cierra con la ventana: mientras juegas no ocupa nada. Solo responde: no ejecuta nada en el equipo. Nada sale de aquí.

--autoprueba: revisa lo que se le entrega al modelo.
--real: baja el modelo y le hace preguntas de verdad (ci/asistente.sh).
"""
import json
import os
import pathlib
import re
import shutil
import statistics
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
TEMP_ALTA = 90  # °C: desde aquí una gráfica de portátil suele empezar a bajar potencia
CALOR_ALTO = 0.05  # parte del tiempo bajando potencia por calor
CAMBIO_DE_TEMP = 5  # °C: menos que esto es lo normal entre sesiones

SISTEMA = """Eres el asistente de Antu OS, un sistema para jugar. Explicas en palabras simples lo que Antu ya calculó sobre un juego.

Reglas:
- Responde en español, en un máximo de cuatro frases cortas y en texto simple, sin listas ni formato.
- Las CONCLUSIONES ya están calculadas y son correctas. Básate en ellas y nunca las contradigas ni agregues otra causa.
- Responde solo lo que te preguntan: usa la conclusión que corresponda y no menciones datos que no vengan al caso.
- Usa los números tal como aparecen. Nunca inventes un número ni un dato.
- Si las conclusiones no alcanzan para responder, dilo y explica qué faltaría medir.
- Nunca pidas abrir una terminal ni escribir comandos. Todo se hace desde las ventanas de Antu.

Qué puede hacer la persona:
- Si el juego rinde menos desde una actualización: en el Observatorio, el botón «Volver atrás» deja la versión anterior para el próximo reinicio. También pudo cambiar un ajuste del juego.
- Si la gráfica se calentó y bajó potencia: despejar las rejillas de ventilación, usar una base con ventilador y elegir el perfil Rendimiento en Zenit.
- Si jugó con batería: conectar el cargador, porque con batería el equipo rinde menos.
- Si no hay fotogramas medidos: se miden al jugar en el modo Eclipse.
- Si el juego se cerró por falta de memoria: cerrar otras aplicaciones, como el navegador, antes de jugar.
- Si un juego no abre o no deja entrar a partidas en línea: la Biblioteca dice si funciona y si su antitrampas lo permite."""


def conclusiones(juego):
    """Lo que se sabe por cálculo, para que el modelo no tenga que deducirlo."""
    ss = juego.get("sesiones", [])
    if not ss:
        return []
    tramos = juego.get("tramos") or [{"desde": 0, "hasta": len(ss) - 1}]

    def del_tramo(tramo, campo):
        return [s[campo] for s in ss[tramo["desde"]:tramo["hasta"] + 1] if s.get(campo)]

    salida = []
    if juego.get("fps"):
        salida.append(f"Ahora da unos {juego['fps']} fotogramas por segundo.")
    else:
        salida.append("Los fotogramas no se midieron: no se puede decir cuántos da. Se miden al jugar en el modo Eclipse.")
    if juego.get("estado") == "baja" and juego.get("detalle"):
        salida.append(juego["titulo"] + ". " + juego["detalle"])

    temps = del_tramo(tramos[-1], "temp")
    calor = max(del_tramo(tramos[-1], "calor"), default=0)
    if temps and max(temps) >= TEMP_ALTA:
        salida.append(f"La gráfica llega a {max(temps):.0f} °C: está caliente.")
    elif temps:
        salida.append(f"La gráfica llega a {max(temps):.0f} °C: es normal para un portátil jugando, no está sobrecalentada.")
    if calor >= CALOR_ALTO:
        salida.append(f"Bajó potencia por calor el {calor * 100:.0f} % del tiempo: el calor sí le está quitando rendimiento.")
    elif temps:
        salida.append("Casi no bajó potencia por calor: el calor no le está quitando rendimiento.")
    if len(tramos) > 1 and temps and del_tramo(tramos[-2], "temp"):
        diferencia = statistics.median(temps) - statistics.median(del_tramo(tramos[-2], "temp"))
        if abs(diferencia) < CAMBIO_DE_TEMP:
            salida.append("La temperatura no cambió con la actualización: no explica ningún cambio de rendimiento.")
        else:
            salida.append(f"Con la actualización, la gráfica quedó {abs(diferencia):.0f} °C más {'caliente' if diferencia > 0 else 'fría'}.")
    if ss[-1].get("energia") == "Batería":
        salida.append("La última sesión fue con batería, y con batería el equipo rinde menos.")
    if juego.get("estado") == "baja":
        if juego.get("cambios") and calor < CALOR_ALTO:
            cambio = "; ".join(juego["cambios"].split("\n"))
            salida.append(f"Lo más probable es que la baja venga de lo que cambió en el sistema ({cambio}). No está demostrado: también pudo cambiar un ajuste del juego.")
        elif calor < CALOR_ALTO:
            salida.append("No se sabe qué causó la baja: lo único seguro es que coincide con la actualización. También pudo cambiar un ajuste del juego.")
    if juego.get("notas"):
        for nota in juego["notas"].split("\n"):
            if "memoria" in nota or "cerró" in nota or "gráfica dejó" in nota or "inválido" in nota:
                salida.append(nota)
    return salida


def contexto(juego):
    """Lo calculado y las mediciones de un juego (lo que arma observatorio.resumir), en palabras para el modelo."""
    lineas = [f"Juego: {juego['nombre']}", "CONCLUSIONES:"] + [f"- {c}" for c in conclusiones(juego)]
    if juego.get("cambios"):
        lineas.append("Qué cambió en el sistema: " + "; ".join(juego["cambios"].split("\n")))
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
    assert "NVIDIA: 1 → 2; Núcleo: 3 → 4" in c
    assert "20 oct" in c and "- 1 oct:" not in c  # solo las últimas
    assert "con cargador" in c
    sin_fps = {"nombre": "J", "titulo": "T", "sesiones": [{"fecha": "1 oct", "fps": 0, "bajo": 0, "temp": 0, "minutos": 1, "energia": "Batería"}]}
    assert "fotogramas sin medir" in contexto(sin_fps) and "peores" not in contexto(sin_fps)
    assert limpiar("<think>hmm</think> Hola") == "Hola" and limpiar("<think>a medias") == ""
    assert mensajes_para(juego, [{"role": "assistant", "content": "a"}], "¿por qué?")[-1]["content"] == "¿por qué?"
    assert modelo_listo(pathlib.Path("/no/existe")) is False

    # Lo calculado, que es lo que el modelo no debe deducir por su cuenta.
    def sesion(temp, calor=0.01, fps=60, energia="Cargador"):
        return {"fecha": "1 oct", "fps": fps, "bajo": 40, "temp": temp, "calor": calor, "minutos": 40, "energia": energia}

    def conclusion(sesiones, tramos=None, **otros):
        base = {"nombre": "J", "titulo": "Rinde 12 % menos", "detalle": "De 66 a 58.", "fps": "58", "estado": "baja", "sesiones": sesiones}
        return " ".join(conclusiones({**base, "tramos": tramos or [{"desde": 0, "hasta": len(sesiones) - 1}], **otros}))

    dos_tramos = [{"desde": 0, "hasta": 0}, {"desde": 1, "hasta": 1}]
    igual = conclusion([sesion(80), sesion(81)], dos_tramos, cambios="NVIDIA: 1 → 2")
    assert "no está sobrecalentada" in igual and "no explica" in igual and "NVIDIA: 1 → 2" in igual and "calor sí" not in igual
    caliente = conclusion([sesion(80), sesion(93, calor=0.3)], dos_tramos, cambios="NVIDIA: 1 → 2")
    assert "está caliente" in caliente and "calor sí" in caliente and "13 °C más caliente" in caliente and "Lo más probable" not in caliente
    assert "No se sabe qué causó" in conclusion([sesion(80), sesion(80)], dos_tramos)
    assert "con batería" in conclusion([sesion(80, energia="Batería")])
    assert "no se midieron" in conclusion([sesion(0, fps=0)], fps="", estado="pocas")
    print("Asistente: lo que recibe el modelo está correcto")


def real():
    """Preguntas de verdad con mediciones inventadas. Falla si no usa los datos o si manda a la terminal."""
    from observatorio import demo, resumir_todo

    caliente = [{"juego": "Caluroso", "appid": 1, "inicio": 1000 + i, "minutos": 40, "fps": f, "fps_bajo": f - 20, "cargador": True,
                 "gpu_temp": t, "calor": c, "version": v, "nvidia": "1", "nucleo": "7.2"}
                for i, (f, t, c, v) in enumerate(((70, 78, 0, "a"), (71, 79, 0, "a"), (55, 94, 0.3, "b"), (54, 95, 0.32, "b")))]
    juegos = {j["nombre"]: j for j in resumir_todo(demo() + caliente)}
    motor = Motor()
    try:
        motor.bajar(lambda f: None)
        fallas = 0
        for nombre, pregunta, debe, no_debe in (
            ("ELDEN RING", "¿Por qué me va más lento?", ("NVIDIA",), ("se calentó más", "redujera la potencia")),
            ("ELDEN RING", "¿Se está calentando demasiado?", ("81", "normal"), ()),
            ("Caluroso", "¿Por qué me va más lento?", ("calor",), ("controlador",)),
            ("Cyberpunk 2077", "¿Por qué se cerró?", ("memoria",), ("°C",)),
            ("Cyberpunk 2077", "¿A cuántos fotogramas corre?", ("medi",), ("°C",)),
        ):
            inicio = time.time()
            respuesta = motor.preguntar(mensajes_para(juegos[nombre], [], pregunta), lambda t: None)
            print(f"\n[{nombre}] {pregunta} ({time.time() - inicio:.0f} s)\n{respuesta}", flush=True)
            texto = respuesta.lower()
            if not all(p.lower() in texto for p in debe) or any(p.lower() in texto for p in (*no_debe, "terminal")):
                print(f"::error::El asistente no respondió con los datos: debía decir {debe} y no decir {no_debe}")
                fallas += 1
        sys.exit(1 if fallas else 0)
    finally:
        motor.cerrar()


if __name__ == "__main__":
    if "--real" in sys.argv:
        real()
    else:
        autoprueba()
