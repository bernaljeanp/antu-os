// Campo de texto en píldora de vidrio, con foco de lava y estado de error.
import QtQuick
import QtQuick.Controls.Basic

TextField {
    id: field

    property real u: 1
    property bool invalid: false

    implicitHeight: 60 * u
    leftPadding: 24 * u
    rightPadding: 24 * u
    color: "#F5F5F7"
    placeholderTextColor: "#A1A1A6"
    selectionColor: "#C93A0C"
    selectedTextColor: "#FFFFFF"
    font.family: "Inter"
    font.pixelSize: 23 * u
    verticalAlignment: TextInput.AlignVCenter
    background: Rectangle {
        radius: height / 2
        color: field.hovered && !field.activeFocus ? Qt.rgba(1, 1, 1, 0.18) : Qt.rgba(1, 1, 1, 0.13)
        border.width: field.activeFocus || field.invalid ? 2 * field.u : 1
        border.color: field.invalid ? "#FF7069" : (field.activeFocus ? "#FF5A1F" : Qt.rgba(1, 1, 1, 0.20))
    }
}
