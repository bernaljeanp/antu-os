// Antu OS, instalador del USB en vivo: elegir el disco, confirmar el borrado, copiar y reiniciar. Idioma, cuenta y
// escritorio se eligen después, en Inicio. Mismo mundo visual que Inicio: vidrio de obsidiana y lava.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "../inicio"

ApplicationWindow {
    id: root
    width: 1100
    height: 720
    minimumWidth: 900
    minimumHeight: 640
    visible: true
    title: "Instalar Antu"
    color: "#0B0B0E"

    readonly property real u: Math.min(width / 1760, height / 1150)
    readonly property color ink: "#F5F5F7"
    readonly property color ink2: "#C7C7CC"
    readonly property color negative: "#FF7069"

    // 0 elegir disco, 1 confirmar, 2 instalando, 3 listo, 4 error
    property int screen: 0
    property var disks: backend.disks()
    property int selected: -1
    readonly property var disk: selected >= 0 && selected < disks.length ? disks[selected] : null
    property int stage: 0
    property string lastLine: ""
    property string error: ""

    function refresh() {
        disks = backend.disks()
        selected = -1
    }
    function install() {
        stage = 0
        lastLine = ""
        screen = 2
        backend.install(disk.path, disk.huella || "")
    }

    // Cerrar a mitad de la copia dejaría el disco a medias.
    onClosing: (close) => { close.accepted = root.screen !== 2 }

    Connections {
        target: backend
        function onStage(index) { root.stage = Math.max(root.stage, index) }
        function onLine(text) { root.lastLine = text }
        function onFinished(ok, message) {
            root.error = message
            root.screen = ok ? 3 : 4
        }
    }

    component Heading: ColumnLayout {
        property alias title: titleText.text
        property alias subtitle: subtitleText.text
        Layout.fillWidth: true
        Layout.bottomMargin: 20 * root.u
        spacing: 10 * root.u
        Text {
            id: titleText
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: root.ink
            font.family: "Inter"
            font.pixelSize: 50 * root.u
            font.weight: Font.Bold
            font.variableAxes: ({ "opsz": 32 })
        }
        Text {
            id: subtitleText
            visible: text.length > 0
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: root.ink2
            font.family: "Inter"
            font.pixelSize: 25 * root.u
        }
    }

    component Body: Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        color: root.ink2
        font.family: "Inter"
        font.pixelSize: 23 * root.u
        lineHeight: 1.15
    }

    component Glass: Rectangle {
        Layout.fillWidth: true
        radius: 18 * root.u
        color: Qt.rgba(1, 1, 1, 0.07)
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.16)
    }

    component DiskRow: AbstractButton {
        id: row
        required property var modelData
        required property int index
        readonly property bool usable: modelData.reason === ""
        readonly property bool chosen: root.selected === index
        Layout.fillWidth: true
        implicitHeight: 132 * root.u
        enabled: usable
        Accessible.name: modelData.name + ", " + modelData.detail + ". " + (usable ? modelData.contents : modelData.reason)
        onClicked: root.selected = index
        onDoubleClicked: root.screen = 1
        background: Rectangle {
            radius: 18 * root.u
            color: row.hovered ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(1, 1, 1, row.usable ? 0.07 : 0.04)
            border.width: row.chosen || row.visualFocus ? 3 * root.u : 1
            border.color: row.chosen || row.visualFocus ? "#FF5A1F" : Qt.rgba(1, 1, 1, 0.16)
            Behavior on color { ColorAnimation { duration: 120 } }
        }
        contentItem: RowLayout {
            spacing: 26 * root.u
            Image {
                Layout.leftMargin: 30 * root.u
                opacity: row.usable ? 1 : 0.5
                source: row.modelData.kind === "usb" ? "usb.svg" : "disco.svg"
                sourceSize.width: 60 * root.u
                sourceSize.height: 60 * root.u
            }
            ColumnLayout {
                Layout.fillWidth: true
                Layout.rightMargin: 30 * root.u
                spacing: 5 * root.u
                Text {
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                    text: row.modelData.name
                    color: row.usable ? root.ink : root.ink2
                    font.family: "Inter"
                    font.pixelSize: 27 * root.u
                    font.weight: Font.DemiBold
                }
                Text {
                    text: row.modelData.detail
                    color: root.ink2
                    font.family: "Inter"
                    font.pixelSize: 21 * root.u
                    font.features: ({ "tnum": 1 })
                }
                Text {
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                    text: row.usable ? row.modelData.contents : row.modelData.reason
                    color: row.usable && row.modelData.windows ? root.negative : root.ink2
                    font.family: "Inter"
                    font.pixelSize: 21 * root.u
                }
            }
        }
    }

    // Fondo: el de Antu, oscurecido. La ventana flota sobre el mismo fondo del escritorio y lo continúa.
    Image {
        anchors.fill: parent
        source: "file:///usr/share/wallpapers/Antu/contents/images_dark/3840x2160.jpg"
        sourceSize.width: 1920
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
    }
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.6
    }

    Flickable {
        id: page
        anchors.fill: parent
        contentHeight: content.implicitHeight + 160 * root.u
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        ColumnLayout {
            id: content
            width: Math.min(1320 * root.u, page.width - 120 * root.u)
            anchors.horizontalCenter: parent.horizontalCenter
            y: 80 * root.u
            spacing: 0

            Image {
                Layout.bottomMargin: 30 * root.u
                source: "file:///usr/share/antu/antu-symbol.svg"
                sourceSize.width: 76 * root.u
                sourceSize.height: 76 * root.u
            }

            StackLayout {
                Layout.fillWidth: true
                currentIndex: root.screen

                // 0. Elegir disco
                ColumnLayout {
                    spacing: 18 * root.u
                    Heading {
                        title: "Instalar Antu"
                        subtitle: "Elige el disco donde vivirá Antu. Ocupará el disco entero."
                    }
                    Repeater {
                        model: root.disks
                        delegate: DiskRow {}
                    }
                    Glass {
                        visible: root.disks.length === 0
                        implicitHeight: emptyText.implicitHeight + 64 * root.u
                        Body {
                            id: emptyText
                            anchors.fill: parent
                            anchors.margins: 32 * root.u
                            text: "No encontramos ningún disco. Conecta uno y pulsa Buscar de nuevo."
                        }
                    }
                    RowLayout {
                        Layout.topMargin: 16 * root.u
                        spacing: 18 * root.u
                        LavaButton {
                            u: root.u
                            primary: false
                            text: "Buscar de nuevo"
                            onClicked: root.refresh()
                        }
                        Item { Layout.fillWidth: true }
                        LavaButton {
                            u: root.u
                            text: "Continuar"
                            enabled: root.disk !== null && root.disk.reason === ""
                            onClicked: root.screen = 1
                        }
                    }
                }

                // 1. Confirmar el borrado
                ColumnLayout {
                    spacing: 18 * root.u
                    Heading {
                        title: "Se borrará todo en este disco"
                        subtitle: root.disk ? root.disk.name + " · " + root.disk.detail : ""
                    }
                    Glass {
                        implicitHeight: partList.implicitHeight + 60 * root.u
                        ColumnLayout {
                            id: partList
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 30 * root.u
                            spacing: 10 * root.u
                            Text {
                                text: root.disk && root.disk.parts.length > 0 ? "Se borrará:" : "El disco está vacío."
                                color: root.ink
                                font.family: "Inter"
                                font.pixelSize: 23 * root.u
                                font.weight: Font.DemiBold
                            }
                            Repeater {
                                model: root.disk ? root.disk.parts : []
                                delegate: Text {
                                    required property string modelData
                                    text: modelData
                                    color: root.ink2
                                    font.family: "Inter"
                                    font.pixelSize: 22 * root.u
                                    font.features: ({ "tnum": 1 })
                                }
                            }
                        }
                    }
                    Body {
                        text: root.disk && root.disk.windows
                              ? "Windows y todos sus archivos desaparecerán de este disco. Si hay algo que quieras conservar, cópialo antes a otro disco o a la nube."
                              : "Si hay algo que quieras conservar, cópialo antes a otro disco o a la nube."
                    }
                    RowLayout {
                        Layout.topMargin: 16 * root.u
                        spacing: 18 * root.u
                        LavaButton {
                            u: root.u
                            primary: false
                            text: "Atrás"
                            onClicked: root.screen = 0
                        }
                        Item { Layout.fillWidth: true }
                        LavaButton {
                            u: root.u
                            destructive: true
                            text: "Borrar e instalar"
                            onClicked: root.install()
                        }
                    }
                }

                // 2. Instalando
                ColumnLayout {
                    spacing: 22 * root.u
                    Heading {
                        title: "Instalando Antu"
                        subtitle: root.disk ? "En " + root.disk.name + "." : ""
                    }
                    // La barra avanza por etapas; el brillo que la recorre dice que sigue trabajando.
                    Rectangle {
                        id: track
                        Layout.fillWidth: true
                        implicitHeight: 12 * root.u
                        radius: height / 2
                        color: Qt.rgba(1, 1, 1, 0.12)
                        Rectangle {
                            id: fill
                            height: parent.height
                            width: track.width * (root.stage + 1) / 3
                            radius: height / 2
                            color: "#FF5A1F"
                            clip: true
                            Behavior on width { NumberAnimation { duration: 700; easing.type: Easing.OutExpo } }
                            Rectangle {
                                property real t: 0
                                width: 220 * root.u
                                height: parent.height
                                x: t * (fill.width + width) - width
                                gradient: Gradient {
                                    orientation: Gradient.Horizontal
                                    GradientStop { position: 0.0; color: "#00FFD2B8" }
                                    GradientStop { position: 0.5; color: "#D9FFD2B8" }
                                    GradientStop { position: 1.0; color: "#00FFD2B8" }
                                }
                                NumberAnimation on t {
                                    from: 0
                                    to: 1
                                    duration: 1600
                                    loops: Animation.Infinite
                                    running: root.screen === 2
                                }
                            }
                        }
                    }
                    Repeater {
                        model: ["Preparar el disco", "Copiar Antu", "Instalar el arranque"]
                        delegate: RowLayout {
                            id: step
                            required property string modelData
                            required property int index
                            readonly property bool done: root.stage > index
                            readonly property bool current: root.stage === index
                            spacing: 18 * root.u
                            Rectangle {
                                implicitWidth: 32 * root.u
                                implicitHeight: implicitWidth
                                radius: width / 2
                                color: step.done ? "#FF5A1F" : "transparent"
                                border.width: step.done ? 0 : 2 * root.u
                                border.color: step.current ? "#FF5A1F" : Qt.rgba(1, 1, 1, 0.38)
                                Image {
                                    anchors.centerIn: parent
                                    visible: step.done
                                    source: "../inicio/check.svg"
                                    sourceSize.width: 18 * root.u
                                    sourceSize.height: 18 * root.u
                                }
                            }
                            Text {
                                text: step.modelData
                                color: step.done || step.current ? root.ink : root.ink2
                                font.family: "Inter"
                                font.pixelSize: 25 * root.u
                                font.weight: step.current ? Font.DemiBold : Font.Normal
                            }
                        }
                    }
                    Body {
                        Layout.topMargin: 8 * root.u
                        text: "Tarda entre 5 y 20 minutos. No apagues el equipo ni quites el USB."
                    }
                    Text {
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                        text: root.lastLine
                        color: root.ink2
                        opacity: 0.8
                        font.family: "JetBrains Mono"
                        font.pixelSize: 18 * root.u
                    }
                }

                // 3. Listo
                ColumnLayout {
                    spacing: 18 * root.u
                    Rectangle {
                        Layout.bottomMargin: 10 * root.u
                        implicitWidth: 88 * root.u
                        implicitHeight: implicitWidth
                        radius: width / 2
                        color: "#FF5A1F"
                        Image {
                            anchors.centerIn: parent
                            source: "../inicio/check.svg"
                            sourceSize.width: 46 * root.u
                            sourceSize.height: 46 * root.u
                        }
                    }
                    Heading {
                        title: "Antu está instalado"
                        subtitle: "Reinicia y quita el USB cuando la pantalla se apague. Al arrancar, Inicio te pedirá tu idioma y tu cuenta."
                    }
                    RowLayout {
                        spacing: 18 * root.u
                        LavaButton {
                            u: root.u
                            primary: false
                            text: "Seguir probando"
                            onClicked: Qt.quit()
                        }
                        Item { Layout.fillWidth: true }
                        LavaButton {
                            u: root.u
                            text: "Reiniciar ahora"
                            onClicked: backend.reboot()
                        }
                    }
                }

                // 4. Error
                ColumnLayout {
                    spacing: 18 * root.u
                    Heading {
                        title: "La instalación no terminó"
                        subtitle: "Tu USB y los demás discos no se tocaron. El registro completo quedó en antu-instalar.log, en tu carpeta personal."
                    }
                    Glass {
                        implicitHeight: errorText.implicitHeight + 56 * root.u
                        Text {
                            id: errorText
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 28 * root.u
                            wrapMode: Text.WrapAnywhere
                            text: root.error
                            color: root.negative
                            font.family: "JetBrains Mono"
                            font.pixelSize: 19 * root.u
                        }
                    }
                    RowLayout {
                        Layout.topMargin: 16 * root.u
                        spacing: 18 * root.u
                        LavaButton {
                            u: root.u
                            primary: false
                            text: "Salir"
                            onClicked: Qt.quit()
                        }
                        Item { Layout.fillWidth: true }
                        LavaButton {
                            u: root.u
                            text: "Volver a intentar"
                            onClicked: {
                                root.refresh()
                                root.screen = 0
                            }
                        }
                    }
                }
            }
        }
    }
}
