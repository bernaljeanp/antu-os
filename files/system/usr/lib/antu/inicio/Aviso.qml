// Aviso de Antu: una placa de vidrio con canto y sombra. El color del aviso tiñe el vidrio desde su ícono, nunca como una raya
// al costado. Sus botones van adentro: Aviso { titulo: "…"; texto: "…"; LavaButton { … } }
import QtQuick
import QtQuick.Layouts

Item {
    id: aviso
    Accessible.role: Accessible.AlertMessage
    Accessible.name: titulo
    Accessible.description: texto

    property real u: 1
    property string titulo
    property string texto
    property string tipo: "atencion"  // atencion, bien, peligro, antu (una invitación: con el símbolo de Antu)
    readonly property color luz: tipo === "bien" ? "#2FA36B" : (tipo === "peligro" ? "#E2392A" : "#FF5A1F")
    readonly property real radio: 20 * u
    default property alias botones: fila.data

    implicitHeight: contenido.implicitHeight + 44 * u

    Halo {
        anchors.fill: parent
        radio: aviso.radio
        alcance: 28 * aviso.u
        fuerza: Antu.dark ? 0.26 : 0.1
        bajada: 14 * aviso.u
    }
    Rectangle {  // el canto recibe la luz desde arriba
        anchors.fill: parent
        radius: aviso.radio
        gradient: Gradient {
            GradientStop { position: 0; color: Qt.rgba(1, 1, 1, 0.34) }
            GradientStop { position: 0.2; color: Qt.rgba(1, 1, 1, 0.1) }
            GradientStop { position: 1; color: Qt.rgba(1, 1, 1, 0.05) }
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: 1
            radius: aviso.radio - 1
            gradient: Gradient {
                GradientStop { position: 0; color: Antu.raised }
                GradientStop { position: 1; color: Antu.window }
            }
            Rectangle {
                anchors.fill: parent
                radius: parent.radius
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: Qt.rgba(aviso.luz.r, aviso.luz.g, aviso.luz.b, 0.2) }
                    GradientStop { position: 0.55; color: Qt.rgba(aviso.luz.r, aviso.luz.g, aviso.luz.b, 0) }
                }
            }
            Reflejo {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: 18 * aviso.u
                y: 1
                fuerza: 0.3
            }
        }
    }
    RowLayout {
        id: contenido
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 22 * aviso.u
        spacing: 18 * aviso.u
        Item {  // el ícono: una pieza con luz propia
            Layout.alignment: Qt.AlignTop
            implicitWidth: 56 * aviso.u
            implicitHeight: 56 * aviso.u
            Halo {
                anchors.fill: parent
                radio: 16 * aviso.u
                tono: aviso.luz
                alcance: 12 * aviso.u
                fuerza: 0.4
                bajada: 4 * aviso.u
            }
            Rectangle {
                anchors.fill: parent
                radius: 16 * aviso.u
                gradient: Gradient {
                    GradientStop { position: 0; color: aviso.tipo === "antu" ? "#3A3A42" : Qt.lighter(aviso.luz, 1.3) }
                    GradientStop { position: 1; color: aviso.tipo === "antu" ? "#16161A" : Qt.darker(aviso.luz, 1.4) }
                }
                Reflejo {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.margins: 8 * aviso.u
                    y: 1
                    fuerza: 0.7
                }
                Image {
                    visible: aviso.tipo === "antu"
                    anchors.centerIn: parent
                    source: "file:///usr/share/antu/antu-symbol.svg"
                    sourceSize.width: 34 * aviso.u
                    sourceSize.height: 34 * aviso.u
                }
                Rectangle {
                    visible: aviso.tipo === "atencion" || aviso.tipo === "peligro"
                    anchors.centerIn: parent
                    anchors.verticalCenterOffset: -6 * aviso.u
                    width: 6 * aviso.u
                    height: 20 * aviso.u
                    radius: width / 2
                    color: "#FFFFFF"
                }
                Rectangle {
                    visible: aviso.tipo === "atencion" || aviso.tipo === "peligro"
                    anchors.centerIn: parent
                    anchors.verticalCenterOffset: 13 * aviso.u
                    width: 7 * aviso.u
                    height: width
                    radius: width / 2
                    color: "#FFFFFF"
                }
                Rectangle {  // visto
                    visible: aviso.tipo === "bien"
                    x: 15 * aviso.u
                    y: 28 * aviso.u
                    width: 6 * aviso.u
                    height: 15 * aviso.u
                    radius: width / 2
                    rotation: -45
                    color: "#FFFFFF"
                }
                Rectangle {
                    visible: aviso.tipo === "bien"
                    x: 27 * aviso.u
                    y: 16 * aviso.u
                    width: 6 * aviso.u
                    height: 27 * aviso.u
                    radius: width / 2
                    rotation: 40
                    color: "#FFFFFF"
                }
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6 * aviso.u
            Text {
                Layout.fillWidth: true
                text: aviso.titulo
                textFormat: Text.PlainText
                wrapMode: Text.WordWrap
                color: Antu.ink
                font.family: "Inter"
                font.pixelSize: Antu.pixels(26, aviso.u)
                font.weight: Font.Bold
            }
            Text {
                Layout.fillWidth: true
                visible: text.length > 0
                text: aviso.texto
                textFormat: Text.PlainText
                wrapMode: Text.WordWrap
                color: Antu.secondary
                font.family: "Inter"
                font.pixelSize: Antu.pixels(21, aviso.u)
                lineHeight: 1.1
            }
            Flow {
                id: fila
                Layout.fillWidth: true
                Layout.topMargin: 16 * aviso.u
                visible: children.length > 0
                spacing: 18 * aviso.u
            }
        }
    }
}
