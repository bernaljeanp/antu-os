// Menú desplegable estándar con el vidrio de Antu: píldora, lista oscura y selección en lava.
import QtQuick
import QtQuick.Controls.Basic

ComboBox {
    id: combo

    property real u: 1

    implicitHeight: 60 * u
    font.family: "Inter"
    font.pixelSize: 23 * u
    leftPadding: 24 * u
    palette.buttonText: "#F5F5F7"
    palette.text: "#F5F5F7"
    palette.window: "#1C1C21"
    palette.base: "#1C1C21"
    palette.highlight: "#C93A0C"
    palette.highlightedText: "#FFFFFF"
    palette.dark: "#C7C7CC"
    background: Rectangle {
        radius: height / 2
        color: combo.hovered ? Qt.rgba(1, 1, 1, 0.18) : Qt.rgba(1, 1, 1, 0.13)
        border.width: combo.visualFocus ? 2 * combo.u : 1
        border.color: combo.visualFocus ? "#FF5A1F" : Qt.rgba(1, 1, 1, 0.20)
    }
}
