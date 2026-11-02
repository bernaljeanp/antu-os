// Antu OS, Informe del equipo: dice qué incluye y qué no, lo crea cuando se pide y explica dónde quedó. Mismo mundo
// visual que el instalador: vidrio de obsidiana y lava.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "../inicio"

ApplicationWindow {
    id: root
    width: 1100
    height: 760
    minimumWidth: 900
    minimumHeight: 660
    visible: true
    title: "Informe del equipo"
    color: "#0B0B0E"

    readonly property real u: Math.min(width / 1760, height / 1216)
    readonly property color ink: "#F5F5F7"
    readonly property color ink2: "#C7C7CC"
    readonly property color ink3: "#8E8E93"
    readonly property color lava: "#FF5A1F"
    readonly property color negative: "#FF7069"

    // 0 inicio, 1 creando, 2 listo, 3 error
    property int screen: 0
    property var resultado: ({})

    Connections {
        target: backend
        function onTerminado(json) {
            root.resultado = JSON.parse(json)
            root.screen = root.resultado.error ? 3 : 2
        }
    }

    component Heading: ColumnLayout {
        property alias title: titleText.text
        property alias subtitle: subtitleText.text
        Layout.fillWidth: true
        Layout.bottomMargin: 26 * root.u
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

    // Tarjeta de vidrio con una lista corta; el punto de color distingue lo que sí va de lo que no.
    component Lista: Rectangle {
        id: lista
        property string titulo
        property var lineas: []
        property color punto: root.lava
        Layout.fillWidth: true
        Layout.preferredWidth: 1
        implicitHeight: contenido.implicitHeight + 56 * root.u
        radius: 18 * root.u
        color: Qt.rgba(1, 1, 1, 0.07)
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.16)
        ColumnLayout {
            id: contenido
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 28 * root.u
            spacing: 14 * root.u
            Text {
                text: lista.titulo
                color: root.ink
                font.family: "Inter"
                font.pixelSize: 25 * root.u
                font.weight: Font.DemiBold
            }
            Repeater {
                model: lista.lineas
                RowLayout {
                    id: fila
                    required property string modelData
                    spacing: 14 * root.u
                    Rectangle {
                        Layout.alignment: Qt.AlignTop
                        Layout.topMargin: 11 * root.u
                        implicitWidth: 8 * root.u
                        implicitHeight: 8 * root.u
                        radius: width / 2
                        color: lista.punto
                    }
                    Text {
                        Layout.fillWidth: true
                        text: fila.modelData
                        wrapMode: Text.WordWrap
                        color: root.ink2
                        font.family: "Inter"
                        font.pixelSize: 22 * root.u
                    }
                }
            }
        }
    }

    // Fondo: el de Antu, oscurecido, como en el instalador.
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
        opacity: 0.62
    }

    ColumnLayout {
        width: Math.min(1240 * root.u, root.width - 120 * root.u)
        anchors.horizontalCenter: parent.horizontalCenter
        y: 80 * root.u
        spacing: 0

        Image {
            Layout.bottomMargin: 26 * root.u
            source: "file:///usr/share/antu/antu-symbol.svg"
            sourceSize.width: 72 * root.u
            sourceSize.height: 72 * root.u
        }

        // 0: qué incluye, registro opcional y crear
        ColumnLayout {
            visible: root.screen === 0
            spacing: 0
            Heading {
                title: "Informe del equipo"
                subtitle: "Reúne lo necesario para revisar cómo funciona Antu en este equipo."
            }
            RowLayout {
                spacing: 20 * root.u
                Lista {
                    titulo: "Incluye"
                    lineas: ["Modelo y piezas del equipo", "Estado de NVIDIA, sonido y wifi",
                             "Temperaturas y ventiladores", "Errores del sistema"]
                }
                Lista {
                    titulo: "No incluye"
                    punto: root.ink3
                    lineas: ["Números de serie", "Direcciones de red ni nombres de wifi",
                             "Lo que hay en tus discos: Windows y tus archivos"]
                }
            }
            Switch {
                id: registro
                Layout.topMargin: 26 * root.u
                text: "Registrar temperaturas y uso de la gráfica mientras pruebo"
                font.family: "Inter"
                font.pixelSize: 23 * root.u
                palette.windowText: root.ink
                palette.text: root.ink
                palette.highlight: "#E2480F"
                palette.mid: Qt.rgba(1, 1, 1, 0.3)
                Accessible.name: text
                onToggled: backend.registrar(checked)
            }
            Body {
                Layout.topMargin: 8 * root.u
                visible: backend.registrando
                text: "Registrando desde hace " + backend.minutos + " min. Deja esta ventana abierta o minimizada mientras "
                      + "juegas; se detiene sola a las 4 horas."
            }
            LavaButton {
                Layout.topMargin: 26 * root.u
                u: root.u
                text: "Crear informe"
                onClicked: {
                    root.screen = 1
                    backend.crear()
                }
            }
            Text {
                Layout.fillWidth: true
                Layout.topMargin: 22 * root.u
                wrapMode: Text.WordWrap
                text: "Nada se sube a internet. Queda en el USB y tú decides si lo compartes."
                color: root.ink3
                font.family: "Inter"
                font.pixelSize: 21 * root.u
            }
        }

        // 1: creando
        ColumnLayout {
            visible: root.screen === 1
            spacing: 0
            Heading {
                title: "Creando el informe…"
                subtitle: "Tarda menos de un minuto."
            }
        }

        // 2: listo
        ColumnLayout {
            visible: root.screen === 2
            spacing: 18 * root.u
            Heading {
                title: root.resultado.usb ? "Informe guardado en el USB" : "Informe guardado en la memoria"
                subtitle: root.resultado.archivo || ""
            }
            Body {
                visible: !!root.resultado.usb
                text: "Al volver a Windows, lo encuentras en la unidad ANTU_DATOS. Si Windows ofrece formatear alguna "
                      + "unidad de este USB, responde que no: se borraría Antu."
            }
            Body {
                visible: !root.resultado.usb
                text: "No encontré la partición de datos del USB, así que quedó en tu carpeta personal. Cópialo a otro "
                      + "USB antes de apagar: al apagar se borra."
            }
            Flow {
                Layout.fillWidth: true
                Layout.topMargin: 10 * root.u
                spacing: 16 * root.u
                LavaButton {
                    u: root.u
                    text: "Ver qué contiene"
                    onClicked: backend.abrir(root.resultado.copia)
                }
                LavaButton {
                    u: root.u
                    primary: false
                    text: "Crear otro"
                    onClicked: root.screen = 0
                }
            }
        }

        // 3: error
        ColumnLayout {
            visible: root.screen === 3
            spacing: 18 * root.u
            Heading {
                title: "No se pudo crear el informe"
            }
            Body {
                text: root.resultado.error || ""
                textFormat: Text.PlainText
                color: root.negative
            }
            LavaButton {
                u: root.u
                primary: false
                text: "Volver"
                onClicked: root.screen = 0
            }
        }
    }
}
