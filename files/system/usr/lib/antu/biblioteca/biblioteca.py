#!/usr/bin/env python3
"""Biblioteca: dice si un juego funciona en Antu antes de instalarlo, y te lleva a Steam para jugarlo o conseguirlo.

La interfaz vive en Biblioteca.qml. El veredicto junta tres fuentes públicas, sin cuenta ni datos personales: Steam
(el juego y la revisión de Valve para SteamOS), ProtonDB (lo que informa la gente) y AreWeAntiCheatYet (si su antitrampas
deja jugar en Linux). El antitrampas manda: de nada sirve que el juego abra si no te deja entrar a las partidas.

--demo: muestra la interfaz con datos fijos y sin conexión (capturas de CI).
--autoprueba: revisa los veredictos.
"""
import json
import locale
import os
import pathlib
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
ECLIPSE = "/usr/bin/antu-eclipse-entrar"
STEAM = pathlib.Path.home() / ".local/share/Steam/steamapps"
HERRAMIENTAS = ("proton", "steam linux runtime", "steamworks")  # las instala Steam: no son juegos
CACHE = pathlib.Path.home() / ".cache/antu/antitrampas.json"
PAIS = (os.environ.get("LANG") or "es_CL")[3:5] or "CL"

URL_ANTITRAMPAS = "https://raw.githubusercontent.com/AreWeAntiCheatYet/AreWeAntiCheatYet/HEAD/games.json"
URL_BUSCAR = "https://store.steampowered.com/api/storesearch/"
URL_DATOS = "https://api.steampowered.com/IStoreBrowseService/GetItems/v1"
URL_MAS_JUGADOS = "https://api.steampowered.com/ISteamChartsService/GetGamesByConcurrentPlayers/v1/"
URL_IMAGENES = "https://shared.steamstatic.com/store_item_assets/"
URL_PROTONDB = "https://www.protondb.com/api/v1/reports/summaries/{}.json"
MAS_JUGADOS = 36

TIERS = {
    "platinum": ("perfecto", "Funciona perfecto"),
    "gold": ("bien", "Funciona bien"),
    "silver": ("ajustes", "Funciona con ajustes"),
    "bronze": ("problemas", "Funciona con problemas"),
    "borked": ("no", "No funciona"),
}
VALVE = {
    3: ("bien", "Funciona bien", "Valve lo verificó para SteamOS."),
    2: ("ajustes", "Funciona con ajustes", "Valve lo marca como jugable en SteamOS, con algún detalle."),
    1: ("no", "No funciona", "Valve lo marca como no compatible con SteamOS."),
}
# Los que no se juegan con su versión de Windows, sino con otro programa que Antu ya trae.
ESPECIALES = {
    "roblox": {
        "nombre": "Roblox", "nivel": "bien", "titulo": "Funciona con Sober",
        "razones": ["Se juega con Sober, que Antu instala en el primer arranque. Sober no es oficial: Roblox no lo apoya.",
                    "La versión de Windows no funciona: su antitrampas, Hyperion, bloquea Linux."],
        "accion": "Abrir en Discover", "enlace": "appstream://org.vinegarhq.Sober",
    },
}


def veredicto(tier=None, informes=0, valve=0, nativo=False, estado_trampa=None, trampas=(), revise_trampas=True):
    """(nivel, título, razones) del juego. nivel: perfecto, bien, ajustes, problemas, no, nada."""
    nivel, titulo, razones = "nada", "Sin datos suficientes", []
    if tier in TIERS:
        nivel, titulo = TIERS[tier]
        razones.append(f"{informes:n} informes de personas que lo jugaron en Linux (ProtonDB).")
    if valve in VALVE:
        if nivel == "nada":
            nivel, titulo = VALVE[valve][:2]
        razones.append(VALVE[valve][2])
    if nativo:
        if nivel == "nada":
            nivel, titulo = "bien", "Funciona bien"
        razones.append("Tiene versión para Linux.")

    nombre = " y ".join(trampas) or "Su antitrampas"
    if estado_trampa == "Denied":
        nivel, titulo = "no", "No funciona"
        razones.insert(0, f"Sus creadores no permiten jugarlo en Linux: {nombre} lo bloquea.")
    elif estado_trampa == "Broken":
        nivel, titulo = "no", "No funciona en línea"
        razones.insert(0, f"{nombre} no funciona en Linux: lo más probable es que no puedas entrar a partidas en línea.")
    elif estado_trampa == "Planned":
        nivel, titulo = "problemas", "Aún no funciona en línea"
        razones.insert(0, f"Sus creadores planean habilitar {nombre} en Linux, pero todavía no.")
    elif estado_trampa == "Running":
        if nivel == "nada":
            nivel, titulo = "ajustes", "Funciona con ajustes"
        razones.insert(0, f"{nombre} funciona en Linux, aunque sin apoyo oficial de sus creadores.")
    elif estado_trampa == "Supported":
        if nivel == "nada":
            nivel, titulo = "bien", "Funciona bien"
        razones.insert(0, f"{nombre} funciona en Linux, con apoyo de sus creadores.")
    elif not revise_trampas:
        razones.append("No pude revisar si tiene antitrampas: míralo antes de comprarlo.")
    if not razones:
        razones.append("Casi nadie ha informado sobre este juego todavía.")
    return nivel, titulo, razones


def normal(nombre):
    return re.sub(r"[^a-z0-9]", "", nombre.lower())


def pedir(url, **parametros):
    if parametros:
        url += "?" + urllib.parse.urlencode(parametros)
    pedido = urllib.request.Request(url, headers={"User-Agent": "Antu-Biblioteca"})
    with urllib.request.urlopen(pedido, timeout=15) as r:
        return json.load(r)


def juegos_instalados():
    """{appid: nombre} de lo instalado en Steam, en todas sus bibliotecas."""
    carpetas = [STEAM]
    try:
        vdf = (STEAM / "libraryfolders.vdf").read_text(errors="replace")
        carpetas += [pathlib.Path(p) / "steamapps" for p in re.findall(r'"path"\s+"([^"]+)"', vdf)]
    except OSError:
        pass
    instalados = {}
    for carpeta in carpetas:
        for manifiesto in carpeta.glob("appmanifest_*.acf"):
            try:
                texto = manifiesto.read_text(errors="replace")
            except OSError:
                continue
            appid = re.search(r'"appid"\s+"(\d+)"', texto)
            nombre = re.search(r'"name"\s+"([^"]+)"', texto)
            if appid and nombre and not nombre[1].lower().startswith(HERRAMIENTAS):
                instalados[int(appid[1])] = nombre[1]
    return instalados


def datos_de_steam(appids):
    """Nombre, imagen y compatibilidad de una vez, solo juegos (nada de programas ni consolas)."""
    if not appids:
        return []
    entrada = {"ids": [{"appid": a} for a in appids],
               "context": {"language": "spanish", "country_code": PAIS},
               "data_request": {"include_assets": True, "include_platforms": True}}
    juegos = []
    for x in pedir(URL_DATOS, input_json=json.dumps(entrada))["response"].get("store_items", []):
        if x.get("type") == 0 and x.get("visible") and x.get("name"):
            activos = x.get("assets") or {}
            imagen = ""
            if activos.get("header") and activos.get("asset_url_format"):
                imagen = URL_IMAGENES + activos["asset_url_format"].replace("${FILENAME}", activos["header"])
            plataformas = x.get("platforms") or {}
            juegos.append({"appid": int(x["appid"]), "nombre": x["name"], "imagen": imagen,
                           "nativo": bool(plataformas.get("steamos_linux")),
                           "valve": plataformas.get("steam_os_compat_category", 0)})
    return juegos


def cargar_antitrampas():
    """La lista de AreWeAntiCheatYet, bajada una vez al día; None si no hay conexión ni copia anterior."""
    def guardada():
        try:
            return json.loads(CACHE.read_text())
        except (OSError, ValueError):
            return None
    try:
        if time.time() - CACHE.stat().st_mtime < 86400 and (datos := guardada()):
            return datos
    except OSError:
        pass
    try:
        datos = pedir(URL_ANTITRAMPAS)
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(datos))
        return datos
    except (OSError, ValueError):
        return guardada()


DEMO = [
    {"nombre": "ELDEN RING", "instalado": True, "v": {"tier": "platinum", "informes": 2107, "valve": 3}},
    {"nombre": "Counter-Strike 2", "instalado": True, "v": {"tier": "gold", "informes": 1840, "valve": 2, "nativo": True,
                                                            "estado_trampa": "Supported", "trampas": ["VAC"]}},
    {"nombre": "Baldur's Gate 3", "v": {"tier": "platinum", "informes": 3120, "valve": 3, "nativo": True}},
    {"nombre": "Hogwarts Legacy", "v": {"tier": "gold", "informes": 980, "valve": 3}},
    {"nombre": "Starfield", "v": {"tier": "silver", "informes": 640, "valve": 2}},
    {"nombre": "Apex Legends", "v": {"tier": "gold", "informes": 512, "estado_trampa": "Denied",
                                     "trampas": ["Easy Anti-Cheat", "Hyperion"]}},
    {"nombre": "Fortnite", "v": {"estado_trampa": "Denied", "trampas": ["Easy Anti-Cheat"]}},
    {"nombre": "Un juego nuevo", "v": {}},
]


def main():
    from PyQt6.QtCore import QObject, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
    from PyQt6.QtGui import QGuiApplication, QIcon
    from PyQt6.QtQml import QQmlApplicationEngine

    class Backend(QObject):
        lista = pyqtSignal(str, str)  # juegos en JSON, y qué decir si no hay ninguno
        revisado = pyqtSignal(str, str)  # clave del juego y su veredicto en JSON

        def __init__(self, demo):
            super().__init__()
            self._demo = demo
            self._pool = ThreadPoolExecutor(8)
            self._turno = 0  # lo que llega de una búsqueda anterior se descarta
            self._trampas_listas = threading.Event()
            self._por_steam, self._por_nombre = {}, {}
            self._hay_trampas = False
            self._instalados = {}
            if not demo:
                self._pool.submit(self._cargar_trampas)

        @pyqtProperty(bool, constant=True)
        def demo(self):
            return self._demo

        def _cargar_trampas(self):
            datos = cargar_antitrampas()
            if isinstance(datos, list):
                for x in datos:
                    if isinstance(x, dict) and x.get("name"):
                        self._por_nombre[normal(x["name"])] = x
                        steam = (x.get("storeIds") or {}).get("steam")
                        if steam:
                            self._por_steam[str(steam)] = x
                self._hay_trampas = True
            self._trampas_listas.set()

        def _publicar(self, turno, juegos, vacio):
            if turno == self._turno:
                self.lista.emit(json.dumps(juegos), vacio)

        def _ficha(self, juego):
            """Lo que la interfaz necesita de un juego de Steam, antes de tener su veredicto."""
            appid = juego["appid"]
            instalado = appid in self._instalados
            return {"clave": f"s{appid}", "appid": appid, "nombre": juego["nombre"], "imagen": juego["imagen"],
                    "instalado": instalado, "nivel": "", "titulo": "Revisando…", "razones": "",
                    "accion": "Jugar" if instalado else "Abrir en Steam",
                    "enlace": f"steam://rungameid/{appid}" if instalado else f"steam://store/{appid}"}

        def _revisar(self, juego):
            informe = {}
            try:
                informe = pedir(URL_PROTONDB.format(juego["appid"]))
            except (OSError, ValueError):
                pass  # sin informes: ProtonDB responde 404
            self._trampas_listas.wait(30)
            trampa = (self._por_steam.get(str(juego["appid"])) or self._por_nombre.get(normal(juego["nombre"]))) or {}
            nivel, titulo, razones = veredicto(informe.get("tier"), informe.get("total", 0), juego["valve"], juego["nativo"],
                                               trampa.get("status"), trampa.get("anticheats") or (), self._hay_trampas)
            self.revisado.emit(f"s{juego['appid']}", json.dumps({"nivel": nivel, "titulo": titulo,
                                                                 "razones": "\n".join(razones)}))

        def _mostrar_steam(self, turno, juegos, primero=(), vacio=""):
            self._publicar(turno, list(primero) + [self._ficha(j) for j in juegos], vacio)
            for juego in juegos:
                self._pool.submit(self._revisar, juego)

        def _fuera_de_steam(self, termino, ya):
            """Los que no están en Steam (Fortnite, Valorant…) también se pueden consultar: es lo que más se pregunta."""
            self._trampas_listas.wait(30)
            hallados = []
            n = normal(termino)
            for clave, especial in ESPECIALES.items():
                if n in clave:
                    hallados.append({"clave": f"x{clave}", "appid": 0, "imagen": "", "instalado": False,
                                     **{k: v for k, v in especial.items() if k != "razones"},
                                     "razones": "\n".join(especial["razones"])})
            for clave, x in self._por_nombre.items():
                if n in clave and clave not in ya and clave not in ESPECIALES and not (x.get("storeIds") or {}).get("steam"):
                    nivel, titulo, razones = veredicto(estado_trampa=x.get("status"), trampas=x.get("anticheats") or ())
                    hallados.append({"clave": f"x{clave}", "appid": 0, "nombre": x["name"], "imagen": "", "instalado": False,
                                     "nivel": nivel, "titulo": titulo, "razones": "\n".join(razones),
                                     "accion": "", "enlace": ""})
            hallados.sort(key=lambda j: normal(j["nombre"]) != n)  # el nombre exacto, primero
            return hallados[:6]

        @pyqtSlot(str)
        def buscar(self, termino):
            self._turno += 1
            self._pool.submit(self._buscar, self._turno, termino.strip())

        def _buscar(self, turno, termino):
            if self._demo:
                return
            try:
                self._instalados = juegos_instalados()
                ids = [x["id"] for x in pedir(URL_BUSCAR, term=termino, l="spanish", cc=PAIS).get("items", [])]
                juegos = datos_de_steam(ids)
            except (OSError, ValueError, KeyError):
                self._publicar(turno, self._fuera_de_steam(termino, set()), "Sin conexión: no pude buscar en Steam.")
                return
            fuera = self._fuera_de_steam(termino, {normal(j["nombre"]) for j in juegos})
            exactos = [j for j in fuera if normal(j["nombre"]) == normal(termino)]
            self._mostrar_steam(turno, juegos, exactos + [j for j in fuera if j not in exactos],
                                f"No encontré «{termino}». Prueba con otro nombre.")

        @pyqtSlot(str)
        def pestana(self, cual):
            self._turno += 1
            self._pool.submit(self._demo_lista if self._demo else self._tus_juegos if cual == "tus" else self._populares,
                              self._turno)

        def _demo_lista(self, turno):
            juegos = []
            for i, d in enumerate(DEMO):
                nivel, titulo, razones = veredicto(**d["v"])
                juegos.append({"clave": f"d{i}", "appid": i + 1, "nombre": d["nombre"], "imagen": "",
                               "instalado": d.get("instalado", False), "nivel": nivel, "titulo": titulo,
                               "razones": "\n".join(razones), "enlace": "",
                               "accion": "Jugar" if d.get("instalado") else "Abrir en Steam"})
            self._publicar(turno, juegos, "")

        def _tus_juegos(self, turno):
            self._instalados = juegos_instalados()
            vacio = "Aún no tienes juegos instalados en Steam. Busca uno o mira los más jugados."
            if not self._instalados:
                self._publicar(turno, [], vacio)
                return
            juegos = []
            try:
                juegos = datos_de_steam(list(self._instalados))
            except (OSError, ValueError, KeyError):
                pass  # sin conexión: igual se muestran, con el nombre que guardó Steam
            faltan = set(self._instalados) - {j["appid"] for j in juegos}
            juegos += [{"appid": a, "nombre": self._instalados[a], "imagen": "", "nativo": False, "valve": 0} for a in faltan]
            juegos.sort(key=lambda j: j["nombre"].lower())
            self._mostrar_steam(turno, juegos, vacio=vacio)

        def _populares(self, turno):
            self._instalados = juegos_instalados()
            try:
                ranking = pedir(URL_MAS_JUGADOS)["response"]["ranks"]
                ids = [r["appid"] for r in ranking[:MAS_JUGADOS]]
                por_id = {j["appid"]: j for j in datos_de_steam(ids)}
            except (OSError, ValueError, KeyError):
                self._publicar(turno, [], "Sin conexión: conéctate a internet para ver los más jugados.")
                return
            self._mostrar_steam(turno, [por_id[a] for a in ids if a in por_id])

        @pyqtSlot()
        def eclipse(self):
            if not self._demo:
                subprocess.Popen([ECLIPSE], start_new_session=True)

    app = QGuiApplication(sys.argv)
    app.setApplicationName("Biblioteca")
    app.setDesktopFileName("antu-biblioteca")
    app.setWindowIcon(QIcon.fromTheme("antu-biblioteca"))
    backend = Backend(demo="--demo" in sys.argv)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(HERE / "Biblioteca.qml")))
    if not engine.rootObjects():
        sys.exit(1)
    sys.exit(app.exec())


def autoprueba():
    v = veredicto
    assert v("platinum", 10)[:2] == ("perfecto", "Funciona perfecto")
    assert v("borked", 10)[0] == "no"
    # El antitrampas manda aunque la gente diga que el juego abre.
    assert v("platinum", 10, estado_trampa="Denied", trampas=["Vanguard"])[:2] == ("no", "No funciona")
    assert "Vanguard" in v("gold", 10, estado_trampa="Denied", trampas=["Vanguard"])[2][0]
    assert v("gold", 10, estado_trampa="Broken")[:2] == ("no", "No funciona en línea")
    assert v("gold", 10, estado_trampa="Planned")[1] == "Aún no funciona en línea"
    assert v("gold", 10, estado_trampa="Supported", trampas=["VAC"])[0] == "bien"
    assert v("silver", 10, estado_trampa="Running")[0] == "ajustes"
    # Sin informes: Valve, luego la versión de Linux; y si no hay nada, se dice.
    assert v(valve=3)[0] == "bien" and v(valve=1)[0] == "no"
    assert v(nativo=True)[0] == "bien"
    assert v()[:2] == ("nada", "Sin datos suficientes") and v()[2]
    # Nunca da por buena la parte en línea sin haberla podido revisar.
    assert any("antitrampas" in r for r in v("gold", 10, revise_trampas=False)[2])
    assert not any("revisar" in r for r in v("gold", 10, estado_trampa="Supported", revise_trampas=False)[2])
    assert normal("Counter-Strike® 2") == "counterstrike2"
    print("Biblioteca: veredictos correctos")


if __name__ == "__main__":
    try:
        locale.setlocale(locale.LC_NUMERIC, "")
    except locale.Error:
        pass
    if "--autoprueba" in sys.argv:
        autoprueba()
    else:
        main()
