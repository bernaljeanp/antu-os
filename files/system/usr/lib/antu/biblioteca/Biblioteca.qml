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
    color: "#0B0B0E"

    readonly property real u: Math.min(width / 1760, height / 1216)
    readonly property color ink: "#F5F5F7"
    readonly property color ink2: "#C7C7CC"
    readonly property color ink3: "#A1A1A6"
    readonly property color lava: "#FF5A1F"

    property string cual: "tus"  // la pestaña: tus, populares
    property string vacio: ""
    property bool cargando: true
    property int elegido: -1
    readonly property var juego: elegido >= 0 && elegido < modelo.count ? modelo.get(elegido) : null

    function colorDe(nivel) {
        return nivel === "perfecto" || nivel === "bien" ? "#57D98B"
             : nivel === "ajustes" ? "#F5C451"
             : nivel === "problemas" ? "#FF9A5C"
             : nivel === "no" ? "#FF7069"
             : "#A1A1A6"
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
            for (const j of JSON.parse(json))
                modelo.append(j)
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

    Image {
        anchors.fill: parent
        source: "file:///usr/share/wallpapers/Paranal/contents/images_dark/3840x2160.jpg"
        sourceSize.width: 1920
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
    }
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.66
    }

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
            font.pixelSize: 25 * root.u
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
            font.pixelSize: sello.tamano * root.u
            font.weight: Font.DemiBold
        }
    }

    // Portada: la de Steam; si no hay, la inicial del juego sobre vidrio.
    component Portada: Rectangle {
        id: portadaBase
        property string imagen
        property string nombre
        color: Qt.rgba(1, 1, 1, 0.06)
        clip: true
        Text {
            anchors.centerIn: parent
            visible: foto.status !== Image.Ready
            text: portadaBase.nombre.charAt(0)
            textFormat: Text.PlainText
            color: Qt.rgba(1, 1, 1, 0.16)
            font.family: "Inter"
            font.pixelSize: 96 * root.u
            font.weight: Font.Bold
        }
        Image {
            id: foto
            anchors.fill: parent
            source: portadaBase.imagen
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 44 * root.u
        anchors.rightMargin: (panel.visible ? panel.width : 0) + 44 * root.u
        spacing: 22 * root.u

        RowLayout {
            spacing: 18 * root.u
            Image {
                source: "file:///usr/share/antu/antu-symbol.svg"
                sourceSize.width: 54 * root.u
                sourceSize.height: 54 * root.u
            }
            Text {
                text: "Biblioteca"
                color: root.ink
                font.family: "Inter"
                font.pixelSize: 44 * root.u
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
            cellHeight: cellWidth * 215 / 460 + 104 * root.u
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
                background: Rectangle {
                    x: 8 * root.u
                    y: 8 * root.u
                    width: parent.width - 16 * root.u
                    height: parent.height - 16 * root.u
                    radius: 16 * root.u
                    color: tarjeta.hovered || root.elegido === tarjeta.index ? Qt.rgba(1, 1, 1, 0.13) : Qt.rgba(1, 1, 1, 0.07)
                    border.width: tarjeta.visualFocus ? 3 * root.u : (root.elegido === tarjeta.index ? 2 * root.u : 1)
                    border.color: tarjeta.visualFocus ? "#FFFFFF"
                                : root.elegido === tarjeta.index ? root.lava : Qt.rgba(1, 1, 1, 0.14)
                    clip: true
                    Behavior on color { ColorAnimation { duration: 120 } }
                    Portada {
                        id: portada
                        x: 1
                        y: 1
                        width: parent.width - 2
                        height: width * 215 / 460
                        radius: 15 * root.u
                        imagen: tarjeta.imagen
                        nombre: tarjeta.nombre
                    }
                    Rectangle {
                        anchors.top: portada.top
                        anchors.right: portada.right
                        anchors.margins: 10 * root.u
                        visible: tarjeta.instalado
                        implicitWidth: instaladoTexto.implicitWidth + 22 * root.u
                        implicitHeight: instaladoTexto.implicitHeight + 10 * root.u
                        radius: height / 2
                        color: Qt.rgba(0, 0, 0, 0.72)
                        Text {
                            id: instaladoTexto
                            anchors.centerIn: parent
                            text: "Instalado"
                            color: root.ink
                            font.family: "Inter"
                            font.pixelSize: 17 * root.u
                            font.weight: Font.Medium
                        }
                    }
                    ColumnLayout {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: portada.bottom
                        anchors.margins: 16 * root.u
                        anchors.topMargin: 12 * root.u
                        spacing: 5 * root.u
                        Text {
                            Layout.fillWidth: true
                            text: tarjeta.nombre
                            textFormat: Text.PlainText
                            elide: Text.ElideRight
                            color: root.ink
                            font.family: "Inter"
                            font.pixelSize: 23 * root.u
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
                font.pixelSize: 25 * root.u
            }
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: "Datos de Steam, ProtonDB y AreWeAntiCheatYet: tus búsquedas van a Steam, y solo el número del juego a ProtonDB. Antu no guarda nada."
            color: root.ink3
            font.family: "Inter"
            font.pixelSize: 18 * root.u
        }
    }

    // El detalle: por qué ese veredicto y qué hacer.
    Rectangle {
        id: panel
        visible: root.juego !== null
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        width: 620 * root.u
        color: "#17171C"
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.14)

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 36 * root.u
            spacing: 20 * root.u
            RowLayout {
                Text {
                    Layout.fillWidth: true
                    text: root.juego ? root.juego.nombre : ""
                    textFormat: Text.PlainText
                    wrapMode: Text.WordWrap
                    color: root.ink
                    font.family: "Inter"
                    font.pixelSize: 34 * root.u
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
                radius: 14 * root.u
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
                    font.pixelSize: 23 * root.u
                    lineHeight: 1.12
                }
            }
            Item { Layout.fillHeight: true }
            Text {
                Layout.fillWidth: true
                visible: !!root.juego && root.juego.appid > 0
                text: "Cada equipo es distinto: los informes vienen de personas con todo tipo de gráficas."
                wrapMode: Text.WordWrap
                color: root.ink3
                font.family: "Inter"
                font.pixelSize: 19 * root.u
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
