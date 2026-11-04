// Campo de texto hundido en el vidrio: sombra adentro arriba, luz en el canto de abajo; al escribir, se enciende en lava.
import QtQuick
import QtQuick.Controls.Basic

TextField {
    id: field

    property real u: 1
    property bool invalid: false
    readonly property bool encendido: activeFocus || invalid
    readonly property color borde: invalid ? "#FF7069" : "#FF5A1F"

    implicitHeight: Math.max(40, 60 * u, font.pixelSize * 1.5 + 12)
    leftPadding: 24 * u
    rightPadding: 24 * u
    color: Antu.ink
    placeholderTextColor: Antu.muted
    selectionColor: "#C93A0C"
    selectedTextColor: "#FFFFFF"
    font.family: "Inter"
    font.pixelSize: Antu.pixels(23, u)
    verticalAlignment: TextInput.AlignVCenter
    background: Item {
        Halo {
            anchors.fill: parent
            radio: 16 * field.u
            tono: field.borde
            alcance: 14 * field.u
            fuerza: field.encendido ? 0.26 : 0
            bajada: 0
        }
        Rectangle {
            anchors.fill: parent
            radius: 16 * field.u
            gradient: Gradient {
                GradientStop { position: 0; color: field.encendido ? field.borde : Qt.rgba(0, 0, 0, 0.6) }
                GradientStop { position: 1; color: field.encendido ? field.borde : Qt.rgba(1, 1, 1, 0.26) }
            }
            Rectangle {
                anchors.fill: parent
                anchors.margins: field.encendido ? 2 * field.u : 1
                radius: 15 * field.u
                gradient: Gradient {
                    GradientStop { position: 0; color: Antu.fieldTop }
                    GradientStop { position: 0.3; color: field.hovered && !field.activeFocus ? Antu.raisedHover : Antu.window }
                    GradientStop { position: 1; color: Antu.fieldBottom }
                }
            }
        }
    }
}
