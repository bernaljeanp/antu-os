// Botón de Antu: principal en lava (lo que hace avanzar), destructivo en rojo (lo que borra) o secundario en vidrio;
// foco visible con teclado.
import QtQuick
import QtQuick.Controls.Basic

Button {
    id: button

    property real u: 1
    property bool primary: true
    property bool destructive: false

    implicitHeight: 60 * u
    leftPadding: 34 * u
    rightPadding: 34 * u
    font.family: "Inter"
    font.pixelSize: 23 * u
    font.weight: Font.DemiBold
    contentItem: Text {
        text: button.text
        font: button.font
        color: button.enabled ? "#FFFFFF" : "#8E8E93"
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
    background: Rectangle {
        radius: height / 2
        color: !button.enabled ? Qt.rgba(1, 1, 1, 0.08)
             : button.destructive ? (button.down ? "#A52314" : (button.hovered ? "#D1301F" : "#C42B1C"))
             : button.primary ? (button.down ? "#C93A0C" : (button.hovered ? "#EC4E12" : "#E2480F"))
             : (button.hovered ? Qt.rgba(1, 1, 1, 0.22) : Qt.rgba(1, 1, 1, 0.14))
        border.width: button.visualFocus ? 3 * button.u : 0
        border.color: "#FFFFFF"
        Behavior on color { ColorAnimation { duration: 120 } }
    }
}
