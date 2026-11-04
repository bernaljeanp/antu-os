// Antu OS, Biblioteca: busca un juego y dice, en palabras simples, si funciona antes de instalarlo. Mismo mundo visual que
// el resto de Antu: vidrio de obsidiana y lava. Los nombres y textos vienen de internet: siempre como texto plano.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "../inicio"

ApplicationWindow {
    id: root
    width: 1280
    height: 820
    minimumWidth: 960
    minimumHeight: 640
    visible: true
    title: "Biblioteca"
    color: Antu.base

    readonly property real u: 0.72
    readonly property color ink: Antu.ink
    readonly property color ink2: Antu.secondary
    readonly property color ink3: Antu.muted
    readonly property color lava: Antu.lava
    readonly property bool compacta: width < 1180 || Antu.textFactor > 1.4

    property string cual: "tus"  // la pestaña: tus, populares
    property string vacio: ""
    property bool cargando: true
    property int elegido: -1
    readonly property var juego: elegido >= 0 && elegido < modelo.count ? modelo.get(elegido) : null

    function colorDe(nivel) {
        return nivel === "perfecto" || nivel === "bien" ? Antu.positive
             : nivel === "ajustes" || nivel === "problemas" ? Antu.warning
             : nivel === "no" ? Antu.negative : Antu.muted
    }

    function pedirLista() {
        cargando = true
        elegido = -1
        modelo.clear()
        if (busqueda.text.trim().length > 0)
            backend.buscar(busqueda.text)
        else
            backend.pestana(cual)
    }

    ListModel { id: modelo }

    Connections {
        target: backend
        function onLista(json, vacio) {
            modelo.clear()
            for (const j of JSON.parse(json)) {
                j.consulta = backend.demo ? "Datos de demostración" : ""
                modelo.append(j)
            }
            root.vacio = vacio
            root.cargando = false
            if (backend.demo)
                root.elegido = 1
        }
        function onRevisado(clave, json) {
            for (let i = 0; i < modelo.count; i++) {
                if (modelo.get(i).clave === clave) {
                    modelo.set(i, JSON.parse(json))
                    return
                }
            }
        }
    }

    Component.onCompleted: pedirLista()
    Shortcut {
        sequence: "Escape"
        onActivated: root.elegido = -1
    }
    Shortcut { sequence: "Alt+Left"; onActivated: root.elegido = -1 }
    Shortcut {
        sequence: "Ctrl+F"
        onActivated: {
            root.elegido = -1
            Qt.callLater(function() { busqueda.forceActiveFocus() })
        }
    }

    AntuBackdrop { anchors.fill: parent; photographic: false }

    // Pestaña: texto simple, con una línea de lava bajo la activa.
    component Pestana: AbstractButton {
        id: pestana
        property string valor
        readonly property bool activa: root.cual === valor && busqueda.text.trim().length === 0
        implicitWidth: rotulo.implicitWidth
        implicitHeight: rotulo.implicitHeight + 16 * root.u
        Accessible.name: text
        onClicked: {
            busqueda.clear()
            root.cual = valor
            root.pedirLista()
        }
        contentItem: Text {
            id: rotulo
            text: pestana.text
            color: pestana.activa ? root.ink : (pestana.hovered ? root.ink2 : root.ink3)
            font.family: "Inter"
            font.pixelSize: Antu.pixels(25, root.u)
            font.weight: pestana.activa ? Font.DemiBold : Font.Medium
        }
        background: Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: (pestana.visualFocus ? 4 : 3) * root.u
            radius: height / 2
            color: pestana.visualFocus ? "#FFFFFF" : root.lava
            visible: pestana.activa || pestana.visualFocus
        }
    }

    // Lo que dice si funciona: siempre color y texto, nunca solo color.
    component Sello: RowLayout {
        id: sello
        property string nivel
        property string titulo
        property real tamano: 21
        spacing: 10 * root.u
        Rectangle {
            implicitWidth: 12 * root.u
            implicitHeight: 12 * root.u
            radius: width / 2
            color: root.colorDe(sello.nivel)
        }
        Text {
            Layout.fillWidth: true
            text: sello.titulo
            textFormat: Text.PlainText
            elide: Text.ElideRight
            color: root.colorDe(sello.nivel)
            font.family: "Inter"
            font.pixelSize: Antu.pixels(sello.tamano, root.u)
            font.weight: Font.DemiBold
        }
    }

    ColumnLayout {
        visible: !(root.compacta && panel.visible)
        anchors.fill: parent
        anchors.margins: 44 * root.u
        anchors.rightMargin: (panel.visible ? panel.width : 0) + 44 * root.u
        spacing: 22 * root.u

        RowLayout {
            spacing: 18 * root.u
            Image {
                source: Antu.symbolSource
                sourceSize.width: 54 * root.u
                sourceSize.height: 54 * root.u
            }
            Text {
                text: "Biblioteca"
                color: root.ink
                font.family: "Inter"
                font.pixelSize: Antu.pixels(44, root.u)
                font.weight: Font.Bold
                font.variableAxes: ({ "opsz": 32 })
            }
            Item { Layout.fillWidth: true }
            LavaButton {
                u: root.u
                primary: false
                text: "Modo Eclipse"
                onClicked: backend.eclipse()
            }
        }

        GlassField {
            id: busqueda
            Layout.fillWidth: true
            u: root.u
            focus: true
            placeholderText: "Busca un juego para saber si funciona, también Fortnite o Valorant"
            Accessible.name: "Buscar un juego"
            onTextEdited: espera.restart()
            Timer {
                id: espera
                interval: 400
                onTriggered: root.pedirLista()
            }
        }

        RowLayout {
            spacing: 32 * root.u
            Pestana { text: "Tus juegos"; valor: "tus" }
            Pestana { text: "Los más jugados"; valor: "populares" }
        }

        GridView {
            id: rejilla
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: modelo
            clip: true
            keyNavigationEnabled: true
            boundsBehavior: Flickable.StopAtBounds
            readonly property int columnas: Math.max(2, Math.floor(width / (392 * root.u)))
            cellWidth: width / columnas
            cellHeight: cellWidth * 215 / 460 + Math.max(104 * root.u, 48 * Antu.textFactor)
            ScrollBar.vertical: ScrollBar { }

            delegate: AbstractButton {
                id: tarjeta
                required property int index
                required property string nombre
                required property string imagen
                required property string nivel
                required property string titulo
                required property bool instalado
                width: rejilla.cellWidth
                height: rejilla.cellHeight
                Accessible.name: nombre + ": " + titulo
                onClicked: root.elegido = index
                contentItem: Item { }
                background: TarjetaDeJuego {
                    u: root.u
                    imagen: tarjeta.imagen
                    nombre: tarjeta.nombre
                    insignia: tarjeta.instalado ? "Instalado" : ""
                    activa: root.elegido === tarjeta.index
                    encima: tarjeta.hovered
                    foco: tarjeta.visualFocus
                    ColumnLayout {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 5 * root.u
                        Text {
                            Layout.fillWidth: true
                            text: tarjeta.nombre
                            textFormat: Text.PlainText
                            elide: Text.ElideRight
                            color: root.ink
                            font.family: "Inter"
                            font.pixelSize: Antu.pixels(23, root.u)
                            font.weight: Font.DemiBold
                        }
                        Sello {
                            Layout.fillWidth: true
                            nivel: tarjeta.nivel
                            titulo: tarjeta.titulo
                        }
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                width: parent.width * 0.7
                visible: rejilla.count === 0
                text: root.cargando ? "Buscando…" : root.vacio
                textFormat: Text.PlainText
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                color: root.ink2
                font.family: "Inter"
                font.pixelSize: Antu.pixels(25, root.u)
            }
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: "Datos de Steam, ProtonDB y AreWeAntiCheatYet: tus búsquedas van a Steam, y solo el número del juego a ProtonDB. Antu no guarda nada."
            color: root.ink3
            font.family: "Inter"
            font.pixelSize: Antu.pixels(18, root.u)
        }
    }

    // El detalle: por qué ese veredicto y qué hacer.
    Rectangle {
        id: panel
        visible: root.juego !== null
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        width: root.compacta ? parent.width : 620 * root.u
        color: Antu.window
        border.width: 1
        border.color: Antu.softEdge

        FocusScroll {
            anchors.fill: parent
            anchors.margins: 36 * root.u
            clip: true
            contentWidth: width
            contentHeight: detalle.implicitHeight
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar { }
        ColumnLayout {
            id: detalle
            width: parent.width
            spacing: 20 * root.u
            RowLayout {
                Text {
                    Layout.fillWidth: true
                    text: root.juego ? root.juego.nombre : ""
                    textFormat: Text.PlainText
                    wrapMode: Text.WordWrap
                    color: root.ink
                    font.family: "Inter"
                    font.pixelSize: Antu.pixels(34, root.u)
                    font.weight: Font.Bold
                }
                LavaButton {
                    Layout.alignment: Qt.AlignTop
                    u: root.u * 0.8
                    primary: false
                    text: "Cerrar"
                    onClicked: root.elegido = -1
                }
            }
            Portada {
                Layout.fillWidth: true
                Layout.preferredHeight: width * 215 / 460
                u: root.u
                radio: 14 * root.u
                visible: !!root.juego && root.juego.imagen.length > 0
                imagen: root.juego ? root.juego.imagen : ""
                nombre: root.juego ? root.juego.nombre : ""
            }
            Sello {
                Layout.fillWidth: true
                tamano: 30
                nivel: root.juego ? root.juego.nivel : ""
                titulo: root.juego ? root.juego.titulo : ""
            }
            Repeater {
                model: root.juego && root.juego.razones.length > 0 ? root.juego.razones.split("\n") : []
                Text {
                    required property string modelData
                    Layout.fillWidth: true
                    text: modelData
                    textFormat: Text.PlainText
                    wrapMode: Text.WordWrap
                    color: root.ink2
                    font.family: "Inter"
                    font.pixelSize: Antu.pixels(23, root.u)
                    lineHeight: 1.12
                }
            }
            Text {
                Layout.fillWidth: true
                visible: !!root.juego && root.juego.appid > 0
                text: "Referencia de otros equipos con Linux. Este juego aún debe comprobarse en tu equipo con Antu."
                wrapMode: Text.WordWrap
                color: root.ink3
                font.family: "Inter"
                font.pixelSize: Antu.pixels(19, root.u)
            }
            Text {
                Layout.fillWidth: true
                text: root.juego && root.juego.consulta ? root.juego.consulta : ""
                visible: text.length > 0
                wrapMode: Text.WordWrap
                color: root.ink3
                font.family: "Inter"
                font.pixelSize: Antu.pixels(18, root.u)
            }
            Flow {
                Layout.fillWidth: true
                spacing: 14 * root.u
                LavaButton {
                    u: root.u
                    visible: !!root.juego && root.juego.accion.length > 0
                    text: root.juego ? root.juego.accion : ""
                    onClicked: Qt.openUrlExternally(root.juego.enlace)
                }
                LavaButton {
                    u: root.u
                    primary: false
                    visible: !!root.juego && root.juego.appid > 0
                    text: "Ver informes"
                    onClicked: Qt.openUrlExternally("https://www.protondb.com/app/" + root.juego.appid)
                }
            }
        }
        }
    }
}
