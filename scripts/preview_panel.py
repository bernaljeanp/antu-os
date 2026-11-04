"""Prueba 4K de las piezas KSVG reales de la barra; no sustituye una sesión Plasma.

Linux: PyQt6 QtQuick, qml6-module-org-kde-ksvg y Breeze. Los iconos de marcas
se leen de --brands, copias locales de sus apps; no se dibujan ni se instalan.
python scripts/preview_panel.py --view states --palette dark
"""
import argparse
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--view", choices=("states", "installed", "live", "mac"), default="states")
    parser.add_argument("--palette", choices=("dark", "light"), default="dark")
    parser.add_argument("--brands", type=Path, default=ROOT / "brand/previews/barra/marcas")
    args = parser.parse_args()
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    os.environ["QT_SCALE_FACTOR"] = "4" if args.view == "states" else "2"
    # KSVG usa la paleta KDE/Kirigami: una configuración temporal evita heredar
    # el azul del escritorio anfitrión o falsear el contraste del tema de Antu.
    config = tempfile.TemporaryDirectory(prefix="antu-panel-config-")
    config_path = Path(config.name)
    os.environ["XDG_CONFIG_HOME"] = str(config_path)
    os.environ["XDG_CACHE_HOME"] = str(config_path / "cache")
    os.environ["KIRIGAMI_PLATFORM_THEME"] = "org.kde.desktop"
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "org.kde.desktop"
    scheme = "AntuObsidiana" if args.palette == "dark" else "AntuSalar"
    colors = (ROOT / f"files/system/usr/share/color-schemes/{scheme}.colors").read_text(encoding="utf-8")
    (config_path / "kdeglobals").write_text("[General]\nColorScheme=" + scheme + "\n" + colors, encoding="utf-8")
    from PyQt6.QtCore import QTimer, QUrl
    from PyQt6.QtGui import QColor, QFontDatabase, QGuiApplication, QPalette
    from PyQt6.QtQuick import QQuickView

    app = QGuiApplication([])
    QFontDatabase.addApplicationFont(str(ROOT / "files/system/usr/share/fonts/antu/Inter-Variable.ttf"))
    dark = args.palette == "dark"
    ink, bg = ("#F5F5F7", "#141418") if dark else ("#1D1D1F", "#F5F5F7")
    palette = QPalette()
    for role, color in ((QPalette.ColorRole.Window, bg), (QPalette.ColorRole.Base, bg),
                        (QPalette.ColorRole.WindowText, ink), (QPalette.ColorRole.Text, ink),
                        (QPalette.ColorRole.ButtonText, ink), (QPalette.ColorRole.Highlight, "#C93A0C"),
                        (QPalette.ColorRole.HighlightedText, "#FFFFFF")):
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    share = ROOT / "files/system/usr/share"
    theme = share / "plasma/desktoptheme/antu"
    provenance = args.brands / "procedencia.json"
    brand_data = json.loads(provenance.read_text(encoding="utf-8")) if provenance.exists() else {}
    brave = brand_data.get("brave", {})
    def icon(name):
        if name == "antu-informe":
            return (share / "icons/Antu/256x256/devices/computer-laptop.png").as_uri()
        if name == "org.kde.dolphin":
            return (share / f"icons/Antu/256x256/apps/{name}.png").as_uri()
        return (share / f"icons/hicolor/256x256/apps/{name}.png").as_uri()
    def status(name):
        for category in ("status", "actions", "devices"):
            path = Path("/usr/share/icons/breeze-dark" if dark else "/usr/share/icons/breeze") / category / "22" / (name + ".svg")
            if path.exists():
                return path.as_uri()
        raise FileNotFoundError("Falta el icono original Breeze: " + name)
    states = [{"label":label,"state":state,"progress":progress,"icon":icon("org.kde.dolphin")}
              for label,state,progress in [("Fijada","",0),("Abierta","south-normal",0),
                  ("Activa","south-focus",0),("Minimizada","south-minimized",0),
                  ("Al pasar","south-normal-hover",0),("Activa al pasar","south-focus-hover",0),
                  ("Atención","south-attention",0),("Progreso","south-normal",0.62)]]
    apps = [("Brave", (args.brands / "brave.png").as_uri(), "")]
    if args.view == "live":
        apps = [("Antu en vivo",icon("antu"),""),("Informe del equipo",icon("antu-informe"),"")]
    apps += [("Dolphin",icon("org.kde.dolphin"),"south-focus"),
             ("Steam",(args.brands / "steam.png").as_uri(),"south-normal"),
             ("Biblioteca",icon("antu-biblioteca"),""),("Observatorio",icon("antu-observatorio"),"")]
    if args.view != "states":
        for name in ("brave.png", "steam.png"):
            if not (args.brands / name).is_file():
                raise FileNotFoundError("Copia local del icono original requerida: " + name)
    tray = [icon("zenit"),status("network-wireless-connected-100"),status("audio-volume-high"),
            status("battery-080"),status("arrow-up")]
    width,height = (960,540) if args.view == "states" else (1920,1080)
    qml = r'''import QtQuick
import org.kde.ksvg as KSvg
Rectangle {
    id: root
    width: previewWidth; height: previewHeight
    color: surface
    Image { anchors.fill: parent; source: wallpaper; visible: viewName !== "states"; fillMode: Image.PreserveAspectCrop }
    Rectangle { anchors.fill: parent; color: surface; opacity: viewName === "states" ? 1 : 0.34 }
    Column {
        x: viewName === "states" ? 40 : 70; y: viewName === "states" ? 38 : 70; spacing: 12
        Text { text: viewName === "states" ? "Antu · estados de las apps" : "Antu · barra de tareas"; color: foreground; font.family: "Inter"; font.pixelSize: viewName === "states" ? 30 : 38; font.weight: Font.DemiBold }
        Text { text: "Revisión 4K · piezas KSVG reales · sesión ilustrativa"; color: secondary; font.family: "Inter"; font.pixelSize: 16 }
    }
    component AppSlot: Item {
        property string taskState: ""
        property string iconSource
        property real progress: 0
        width: 64; height: 48
        KSvg.FrameSvgItem { anchors.fill: parent; imagePath: taskSvg; prefix: parent.taskState; visible: parent.taskState.length > 0 }
        KSvg.FrameSvgItem { x: 0; y: 0; width: parent.width * parent.progress; height: parent.height; imagePath: taskSvg; prefix: "south-progress"; visible: parent.progress > 0 }
        Image {
            readonly property bool windowsLogo: parent.iconSource.endsWith("/brave.png") && braveClip.length === 4
            width: 36; height: 36; anchors.centerIn: parent; source: parent.iconSource
            sourceSize.width: windowsLogo ? braveSourceSize : 256
            sourceSize.height: windowsLogo ? braveSourceSize : 256
            sourceClipRect: windowsLogo ? Qt.rect(braveClip[0],braveClip[1],braveClip[2],braveClip[3]) : undefined
            fillMode: Image.PreserveAspectFit; mipmap: true
        }
    }
    Row {
        visible: viewName === "states"
        anchors.horizontalCenter: parent.horizontalCenter; y: 172; spacing: 10
        Repeater {
            model: stateModel
            delegate: Column {
                required property var modelData
                width: 100; spacing: 18
                AppSlot { anchors.horizontalCenter: parent.horizontalCenter; taskState: modelData.state; iconSource: modelData.icon; progress: modelData.progress }
                Text { width: parent.width; text: modelData.label; color: foreground; font.family: "Inter"; font.pixelSize: 14; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter }
            }
        }
    }
    Column {
        visible: viewName === "states"; x: 40; y: 370; width: parent.width - 80; spacing: 14
        Text { width: parent.width; text: "El punto identifica una app abierta; la marca lava y más larga identifica la activa."; color: foreground; font.family: "Inter"; font.pixelSize: 18; wrapMode: Text.WordWrap }
        Text { width: parent.width; text: "Los lanzadores sin ventana no llevan marca. El progreso mostrado es un ejemplo; Plasma aporta el valor real."; color: secondary; font.family: "Inter"; font.pixelSize: 14; wrapMode: Text.WordWrap }
    }
    Item {
        id: panel
        visible: viewName !== "states"
        x: viewName === "mac" ? (parent.width-width)/2 : 12
        y: parent.height - height - 12
        width: viewName === "mac" ? appsRow.width + 20 : parent.width - 24
        height: 56
        KSvg.FrameSvgItem { anchors.fill: parent; imagePath: panelSvg }
        Row {
            id: appsRow; anchors.centerIn: parent; spacing: 0
            Image { visible: viewName !== "mac"; width: 48; height: 48; source: antuIcon; sourceSize.width: 256; fillMode: Image.PreserveAspectFit }
            Repeater { model: appModel; delegate: AppSlot { required property var modelData; iconSource: modelData.icon; taskState: modelData.state } }
        }
        Row {
            visible: viewName !== "mac"; anchors.right: parent.right; anchors.rightMargin: 16; anchors.verticalCenter: parent.verticalCenter; spacing: 8
            Repeater { model: trayModel; delegate: Image { required property string modelData; width: 22; height: 22; source: modelData; sourceSize.width: 128; sourceSize.height: 128; fillMode: Image.PreserveAspectFit } }
            Item { width: 4; height: 22 }
            Text { text: "mar 3 nov  22:45"; color: foreground; font.family: "Inter"; font.pixelSize: 16; font.weight: Font.Medium }
        }
    }
    Item {
        visible: viewName === "mac"; width: parent.width; height: 34
        KSvg.FrameSvgItem { anchors.fill: parent; imagePath: panelSvg }
        Image { x: 14; y: 5; width: 24; height: 24; source: antuIcon; sourceSize.width: 256; fillMode: Image.PreserveAspectFit }
        Row { anchors.right: parent.right; anchors.rightMargin: 18; anchors.verticalCenter: parent.verticalCenter; spacing: 8
            Repeater { model: trayModel; delegate: Image { required property string modelData; width: 22; height: 22; source: modelData; sourceSize.width: 128; fillMode: Image.PreserveAspectFit } }
            Item { width: 4; height: 22 }
            Text { text: "mar 3 nov  22:45"; color: foreground; font.family: "Inter"; font.pixelSize: 16 }
        }
    }
}'''
    output = ROOT / "brand/previews/barra"
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="antu-panel-") as folder:
        file = Path(folder) / "Panel.qml"
        file.write_text(qml,encoding="utf-8")
        view = QQuickView()
        view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
        context = view.rootContext()
        values = {"previewWidth":width,"previewHeight":height,"surface":bg,"foreground":ink,
                  "secondary":"#C7C7CC" if dark else "#4F4F57", "viewName":args.view,
                  "taskSvg":str(theme/"widgets/tasks.svg"),"panelSvg":str(theme/"translucent/widgets/panel-background.svg"),
                  "wallpaper":(share/"wallpapers/Paranal/contents"/("images_dark" if dark else "images")/"3840x2160.jpg").as_uri(),
                  "stateModel":states,"appModel":[{"label":n,"icon":i,"state":s} for n,i,s in apps],
                  "trayModel":tray,"antuIcon":icon("antu")}
        values.update(braveClip=brave.get("clip", []), braveSourceSize=brave.get("source_size", 600))
        for key,value in values.items(): context.setContextProperty(key,value)
        view.setSource(QUrl.fromLocalFile(str(file)))
        if view.status() != QQuickView.Status.Ready:
            raise RuntimeError("No carga el ensayo nativo KSVG")
        view.resize(width,height);view.show()
        def capture():
            image = view.grabWindow()
            assert (image.width(),image.height()) == (3840,2160)
            name = f"panel-{args.view}-{args.palette}-4k"
            image.save(str(output/(name+".png")))
            (output/(name+".json")).write_text(json.dumps({"view":args.view,"palette":args.palette,
                "size":[image.width(),image.height()],"dpr":view.devicePixelRatio(),
                "renderer":"Qt Quick + real KSVG FrameSvgItem, software; assembled review scene, not Plasma session",
                "zenit":"Tray only; no permanent launcher in task row"},indent=2)+"\n",encoding="utf-8")
            print(name, image.width(),image.height(),flush=True)
            app.quit()
        QTimer.singleShot(1200,capture)
        app.exec()
    config.cleanup()


if __name__ == "__main__":
    main()
