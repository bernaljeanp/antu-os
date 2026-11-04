// Menú desplegable estándar con el vidrio de Antu: píldora, lista oscura y selección en lava.
import QtQuick
import QtQuick.Controls.Basic

ComboBox {
    id: combo

    property real u: 1

    implicitHeight: Math.max(40, 60 * u, font.pixelSize * 1.5 + 12)
    font.family: "Inter"
    font.pixelSize: Antu.pixels(23, u)
    leftPadding: 24 * u
    palette.buttonText: Antu.ink
    palette.text: Antu.ink
    palette.window: Antu.window
    palette.base: Antu.base
    palette.highlight: "#C93A0C"
    palette.highlightedText: "#FFFFFF"
    palette.dark: Antu.edge
    background: Rectangle {
        radius: height / 2
        color: combo.hovered ? Antu.raisedHover : Antu.raised
        border.width: combo.visualFocus ? 2 * combo.u : 1
        border.color: combo.visualFocus ? Antu.lava : Antu.edge
    }
}
