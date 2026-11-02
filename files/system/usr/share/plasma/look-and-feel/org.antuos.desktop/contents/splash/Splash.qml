// Antu OS: pantalla de carga de la sesión. Continúa la animación de arranque: la cumbre sobre negro y la línea de lava
// que avanza mientras Plasma abre el escritorio.
import QtQuick

Rectangle {
    id: root
    color: "#000000"

    property int stage  // lo fija ksplash: de 1 a 6 según avanza la sesión

    Image {
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -root.height * 0.02
        source: "file:///usr/share/antu/antu-symbol.svg"
        sourceSize.width: root.height * 0.1
        sourceSize.height: root.height * 0.1
    }
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        anchors.verticalCenterOffset: root.height * 0.07
        width: root.height * 0.16
        height: Math.max(2, root.height * 0.003)
        radius: height / 2
        color: Qt.rgba(1, 1, 1, 0.12)

        Rectangle {
            height: parent.height
            radius: parent.radius
            width: parent.width * Math.min(root.stage, 6) / 6
            color: "#FF5A1F"
            Behavior on width {
                NumberAnimation {
                    duration: 600
                    easing.type: Easing.OutCubic
                }
            }
        }
    }
}
