#!/usr/bin/env python3
"""Observatorio: cómo rinde cada juego a lo largo del tiempo, y si una actualización lo empeoró.

La interfaz vive en Observatorio.qml. Las sesiones las escribe observador.py, que mide desde afuera: nada se carga dentro del
juego, así que no hay nada que moleste a un antitrampas. Todo queda en este equipo.

Solo se comparan sesiones largas y con la misma fuente de energía, y se dice qué cambió; también pudo cambiar un ajuste del
juego, y eso Antu no lo puede ver: por eso propone volver atrás, nunca lo hace solo.

--demo: muestra la interfaz con datos fijos (capturas de CI).
--autoprueba: revisa la comparación.
"""
import json
import pathlib
import statistics
import subprocess
import sys
import tempfile
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
ARCHIVO = pathlib.Path.home() / ".local/share/antu/observatorio/sesiones.jsonl"
HELPER = "/usr/lib/antu/actualizar-helper"
URL_IMAGEN = "https://shared.steamstatic.com/store_item_assets/steam/apps/{}/header.jpg"
MINUTOS_MINIMOS = 5  # una sesión más corta suele ser un menú: no dice cómo rinde el juego
SESIONES_MINIMAS = 2  # por versión: una sola puede ser una escena distinta
CAMBIO = 0.10  # menos que esto se confunde con el ruido normal entre sesiones
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre",
         "diciembre")


def fecha(t, larga=True):
    d = time.localtime(t)
    return f"{d.tm_mday} de {MESES[d.tm_mon - 1]}" if larga else f"{d.tm_mday} {MESES[d.tm_mon - 1][:3]}"


def leer_sesiones(archivo=ARCHIVO):
    sesiones = []
    try:
        with open(archivo, encoding="utf-8") as f:
            for linea in f:
                try:
                    s = json.loads(linea)
                except ValueError:
                    continue  # una línea a medio escribir no debe borrar el resto
                if isinstance(s, dict) and s.get("juego") and isinstance(s.get("inicio"), (int, float)):
                    sesiones.append(s)
    except OSError:
        pass
    return sesiones


def que_cambio(antes, ahora):
    cambios = []
    for clave, nombre in (("nvidia", "Controlador NVIDIA"), ("nucleo", "Núcleo del sistema")):
        if antes.get(clave) and ahora.get(clave) and antes[clave] != ahora[clave]:
            cambios.append(f"{nombre}: {antes[clave]} → {ahora[clave]}")
    return cambios


def notas_de(s):
    """Lo que dice la última sesión, en palabras simples."""
    notas = []
    if s.get("fallo"):
        notas.append(s["fallo"])
    if s.get("fps") and s.get("fps_bajo"):
        notas.append(f"En sus peores momentos bajó a {s['fps_bajo']:.0f} fotogramas por segundo.")
    if s.get("calor", 0) >= 0.05:
        notas.append(f"Se calentó y bajó potencia durante el {s['calor'] * 100:.0f} % del tiempo.")
    if s.get("gpu_temp"):
        notas.append(f"La gráfica llegó a {s['gpu_temp']:.0f} °C.")
    if s.get("cargador") is False:
        notas.append("Jugaste con batería: el equipo rinde menos para que dure más.")
    return notas


def resumir(nombre, sesiones):
    """Todo lo que la interfaz muestra de un juego."""
    ss = sorted(sesiones, key=lambda s: s["inicio"])
    ultima = ss[-1]
    tramos = []  # sesiones seguidas con la misma versión del sistema
    for i, s in enumerate(ss):
        if tramos and tramos[-1]["version"] == s.get("version"):
            tramos[-1]["hasta"] = i
        else:
            tramos.append({"version": s.get("version"), "desde": i, "hasta": i})

    def validas(tramo, cargador=None):
        return [s["fps"] for s in ss[tramo["desde"]:tramo["hasta"] + 1]
                if s.get("fps") and s.get("minutos", 0) >= MINUTOS_MINIMOS
                and (cargador is None or s.get("cargador") == cargador)]

    for t in tramos:
        v = validas(t)
        t["fps"] = statistics.median(v) if v else None

    estado, titulo, detalle, cambios = "pocas", "Aún no se puede comparar", "", []
    ahora = validas(tramos[-1], ultima.get("cargador"))
    anterior = next((t for t in reversed(tramos[:-1])
                     if len(validas(t, ultima.get("cargador"))) >= SESIONES_MINIMAS), None)
    if not any(s.get("fps") for s in ss):
        titulo = "No se midieron los fotogramas"
        detalle = "En esta forma de jugar no se pudieron medir. Lo demás que se midió está abajo."
    elif len(ss) == 1:
        titulo, detalle = "Primera medición", "Con más sesiones vas a ver cómo cambia."
    elif len(tramos) == 1:
        estado, titulo = "estable", "Rinde parejo"
        detalle = "Todavía no ha cambiado la versión del sistema desde que lo juegas."
    elif len(ahora) < SESIONES_MINIMAS or not anterior:
        detalle = "Hubo una actualización. Con un par de sesiones más se puede comparar."
    else:
        a, b = statistics.median(validas(anterior, ultima.get("cargador"))), statistics.median(ahora)
        cambio = b / a - 1
        desde = fecha(ss[tramos[-1]["desde"]]["inicio"])
        porcentaje = f"{abs(cambio) * 100:.0f} %"
        condicion = "con el cargador conectado" if ultima.get("cargador") else "con batería"
        detalle = f"De {a:.0f} a {b:.0f} fotogramas por segundo, comparando sesiones {condicion}."
        if cambio <= -CAMBIO:
            estado, titulo = "baja", f"Rinde {porcentaje} menos desde la actualización del {desde}"
            cambios = que_cambio(ss[anterior["hasta"]], ss[tramos[-1]["desde"]])
        elif cambio >= CAMBIO:
            estado, titulo = "sube", f"Rinde {porcentaje} más desde la actualización del {desde}"
            cambios = que_cambio(ss[anterior["hasta"]], ss[tramos[-1]["desde"]])
        else:
            estado, titulo = "estable", "Rinde igual que antes de la actualización"

    fps = tramos[-1]["fps"] or ultima.get("fps")
    etiqueta = {"baja": titulo.split(" desde")[0], "sube": titulo.split(" desde")[0], "estable": "Rinde parejo",
                "pocas": "Aún sin comparar"}[estado]
    return {
        "clave": str(ultima.get("appid") or nombre), "nombre": nombre, "estado": estado, "etiqueta": etiqueta,
        "titulo": titulo, "detalle": detalle, "cambios": "\n".join(cambios), "notas": "\n".join(notas_de(ultima)),
        "imagen": URL_IMAGEN.format(int(ultima["appid"])) if ultima.get("appid") else "",
        "fps": f"{fps:.0f}" if fps else "", "reciente": ultima["inicio"],
        "sesiones": [{"fecha": fecha(s["inicio"], False), "fps": s.get("fps") or 0, "bajo": s.get("fps_bajo") or 0,
                      "minutos": s.get("minutos", 0), "temp": s.get("gpu_temp") or 0,
                      "energia": "Cargador" if s.get("cargador") else "Batería"} for s in ss],
        "tramos": [{"desde": t["desde"], "hasta": t["hasta"], "fps": t["fps"] or 0,
                    "fecha": fecha(ss[t["desde"]]["inicio"], False)} for t in tramos],
    }


def resumir_todo(sesiones):
    por_juego = {}
    for s in sesiones:
        por_juego.setdefault(s["juego"], []).append(s)
    juegos = [resumir(nombre, ss) for nombre, ss in por_juego.items()]
    # Primero lo que hay que mirar; después, lo último que jugaste.
    juegos.sort(key=lambda j: (j["estado"] != "baja", -j["reciente"]))
    return juegos


def demo():
    hoy = time.time()
    dia = 86400
    version = lambda v, nvidia: {"version": v, "nvidia": nvidia, "nucleo": "7.2.14"}
    sesiones = []
    for i, (fps, bajo) in enumerate(((67, 49), (65, 48), (68, 50), (64, 47), (66, 49), (58, 41), (59, 42), (57, 39), (58, 41))):
        sesiones.append({"juego": "ELDEN RING", "appid": 1245620, "inicio": hoy - (9 - i) * 3 * dia, "minutos": 45,
                         "fps": fps, "fps_bajo": bajo, "gpu_temp": 79 + i % 3, "calor": 0.02, "cargador": True,
                         **(version("a", "590.48") if i < 5 else version("b", "595.12"))})
    for nombre, appid, base in (("Counter-Strike 2", 730, 214), ("Baldur's Gate 3", 1086940, 74)):
        for i in range(6):
            sesiones.append({"juego": nombre, "appid": appid, "inicio": hoy - (6 - i) * 2 * dia, "minutos": 60,
                             "fps": base + i % 3, "fps_bajo": base * 0.7, "gpu_temp": 74, "cargador": True,
                             **(version("a", "590.48") if i < 3 else version("b", "595.12"))})
    sesiones.append({"juego": "Hades II", "appid": 1145350, "inicio": hoy - dia, "minutos": 30, "fps": 120, "fps_bajo": 96,
                     "gpu_temp": 66, "cargador": False, **version("b", "595.12")})
    sesiones.append({"juego": "Cyberpunk 2077", "appid": 1091500, "inicio": hoy - 2 * dia, "minutos": 12, "gpu_temp": 70, "cargador": True,
                     "fallo": "El equipo se quedó sin memoria y el sistema cerró el juego.", **version("b", "595.12")})
    return sesiones


def main():
    from PyQt6.QtCore import QObject, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
    from PyQt6.QtGui import QGuiApplication, QIcon
    from PyQt6.QtQml import QQmlApplicationEngine

    class Backend(QObject):
        terminado = pyqtSignal(str)

        def __init__(self, es_demo):
            super().__init__()
            self._demo = es_demo
            self._juegos = resumir_todo(demo() if es_demo else leer_sesiones())

        @pyqtProperty(bool, constant=True)
        def demo(self):
            return self._demo

        @pyqtProperty(str, constant=True)
        def juegos(self):
            return json.dumps(self._juegos)

        @pyqtSlot()
        def volver(self):
            if not self._demo:
                threading.Thread(target=self._volver, daemon=True).start()

        def _volver(self):
            try:
                r = subprocess.run(["pkexec", HELPER, "volver"], capture_output=True, text=True, errors="replace", timeout=300)
            except (OSError, subprocess.SubprocessError) as e:
                self.terminado.emit(str(e))
                return
            self.terminado.emit("" if r.returncode == 0 else (r.stderr.strip() or "No se pudo preparar la versión anterior."))

    app = QGuiApplication(sys.argv)
    app.setApplicationName("Observatorio")
    app.setDesktopFileName("antu-observatorio")
    app.setWindowIcon(QIcon.fromTheme("utilities-system-monitor"))
    backend = Backend("--demo" in sys.argv)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(HERE / "Observatorio.qml")))
    if not engine.rootObjects():
        sys.exit(1)
    sys.exit(app.exec())


def autoprueba():
    def sesion(i, fps, version, cargador=True, minutos=40, **otros):
        return {"juego": "J", "inicio": 1000 + i, "minutos": minutos, "fps": fps, "version": version, "cargador": cargador, **otros}

    def de(*ss):
        return resumir("J", list(ss))

    def serie(antes, despues, **kw):
        return [sesion(i, f, "a", **kw) for i, f in enumerate(antes)] + [sesion(10 + i, f, "b", **kw) for i, f in enumerate(despues)]

    assert de(*serie([66, 67], [58, 57], nvidia="1"))["estado"] == "baja"
    assert "menos" in de(*serie([66, 67], [58, 57]))["titulo"]
    assert de(*serie([58, 57], [66, 67]))["estado"] == "sube"
    assert de(*serie([66, 67], [64, 65]))["estado"] == "estable"  # bajo el umbral: es ruido
    assert de(*serie([66], [58, 57]))["estado"] == "pocas"  # falta con qué comparar
    assert de(*serie([66, 67], [58]))["estado"] == "pocas"
    assert de(sesion(0, 60, "a"), sesion(1, 60, "a"))["estado"] == "estable"  # sin actualización de por medio
    assert de(sesion(0, None, "a"))["estado"] == "pocas" and de(sesion(0, None, "a"))["fps"] == ""
    # La batería no se confunde con una mala actualización.
    con_bateria = [sesion(0, 66, "a"), sesion(1, 67, "a"), sesion(10, 30, "b", cargador=False), sesion(11, 31, "b", cargador=False)]
    assert de(*con_bateria)["estado"] == "pocas"
    # Un menú de un minuto no cuenta.
    assert de(*serie([66, 67], [10, 12], minutos=1))["estado"] == "pocas"
    # Dice qué cambió.
    cambio = [sesion(0, 66, "a", nvidia="1"), sesion(1, 66, "a", nvidia="1"), sesion(9, 50, "b", nvidia="2"), sesion(10, 50, "b", nvidia="2")]
    assert "1 → 2" in de(*cambio)["cambios"]
    # Lo que empeoró va primero.
    juegos = resumir_todo([sesion(0, 90, "a") | {"juego": "Otro"}, *serie([66, 67], [58, 57])])
    assert juegos[0]["nombre"] == "J"
    # Una línea rota no borra el resto.
    with tempfile.TemporaryDirectory() as d:
        prueba = pathlib.Path(d) / "sesiones.jsonl"
        prueba.write_text('{"juego": "J", "inicio": 1}\nlínea rota\n[]\n', encoding="utf-8")
        assert len(leer_sesiones(prueba)) == 1
    print("Observatorio: comparación correcta")


if __name__ == "__main__":
    if "--autoprueba" in sys.argv:
        autoprueba()
    else:
        main()
