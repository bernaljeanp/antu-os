// Tarjeta de un juego: la portada arriba, fundida con el cuerpo, y un canto que recibe la luz. Se enciende en lava al elegirla, y
// alerta la hace verse desde lejos. Lo de abajo va adentro: TarjetaDeJuego { imagen: "…"; nombre: "…"; RowLayout { … } }
import QtQuick

Item {
    id: tarjeta

    property real u: 1
    property string imagen
    property string nombre
    property string insignia
    property bool activa: false
    property bool encima: false
    property bool foco: false
    property bool alerta: false
    readonly property real radio: 18 * u
    default property alias contenido: cuerpo.data

    Item {
        x: 10 * tarjeta.u
        y: 10 * tarjeta.u
        width: parent.width - 20 * tarjeta.u
        height: parent.height - 20 * tarjeta.u
        Halo {
            anchors.fill: parent
            radio: tarjeta.radio
            tono: tarjeta.alerta ? "#FF5A1F" : "#000000"
            alcance: (tarjeta.alerta ? 20 : 12) * tarjeta.u
            fuerza: Antu.dark ? (tarjeta.alerta ? 0.18 : 0.18) : 0.08
            bajada: 7 * tarjeta.u
        }
        Rectangle {  // el canto
            anchors.fill: parent
            radius: tarjeta.radio
            gradient: Gradient {
                GradientStop { position: 0; color: tarjeta.activa || tarjeta.alerta ? "#FF8A4C" : Qt.rgba(1, 1, 1, tarjeta.encima ? 0.42 : 0.26) }
                GradientStop { position: 0.3; color: tarjeta.activa ? "#FF5A1F" : Qt.rgba(1, 1, 1, 0.08) }
                GradientStop { position: 1; color: tarjeta.activa ? "#E2480F" : Qt.rgba(1, 1, 1, 0.05) }
            }
            Rectangle {  // el cuerpo
                id: cara
                anchors.fill: parent
                anchors.margins: tarjeta.activa ? 2 * tarjeta.u : 1
                radius: tarjeta.radio - (tarjeta.activa ? 2 * tarjeta.u : 1)
                gradient: Gradient {
                    GradientStop { position: 0; color: tarjeta.encima ? Antu.raisedHover : Antu.raised }
                    GradientStop { position: 1; color: Antu.window }
                }
                Portada {
                    id: portada
                    width: parent.width
                    height: width * 215 / 460
                    u: tarjeta.u
                    radio: cara.radius
                    fundida: true
                    imagen: tarjeta.imagen
                    nombre: tarjeta.nombre
                }
                Rectangle {
                    visible: tarjeta.insignia.length > 0
                    anchors.top: parent.top
                    anchors.right: parent.right
                    anchors.margins: 12 * tarjeta.u
                    implicitWidth: textoInsignia.implicitWidth + 24 * tarjeta.u
                    implicitHeight: textoInsignia.implicitHeight + 12 * tarjeta.u
                    radius: 10 * tarjeta.u
                    color: Antu.raised
                    border.width: 1
                    border.color: Qt.rgba(1, 1, 1, 0.18)
                    Text {
                        id: textoInsignia
                        anchors.centerIn: parent
                        text: tarjeta.insignia
                        color: Antu.ink
                        font.family: "Inter"
                        font.pixelSize: Antu.pixels(17, tarjeta.u)
                        font.weight: Font.Medium
                    }
                }
                Item {
                    id: cuerpo
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: portada.bottom
                    anchors.bottom: parent.bottom
                    anchors.leftMargin: 16 * tarjeta.u
                    anchors.rightMargin: 16 * tarjeta.u
                }
            }
        }
        Rectangle {  // foco con teclado
            visible: tarjeta.foco
            anchors.fill: parent
            anchors.margins: -4 * tarjeta.u
            radius: tarjeta.radio + 4 * tarjeta.u
            color: "transparent"
            border.width: 2.5 * tarjeta.u
            border.color: Antu.ink
        }
    }
}
