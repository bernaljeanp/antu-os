// Luz en el borde de arriba: se apaga hacia los lados, como un reflejo real.
import QtQuick

Rectangle {
    id: reflejo

    property real fuerza: 0.5

    height: 1.5
    gradient: Gradient {
        orientation: Gradient.Horizontal
        GradientStop { position: 0; color: Qt.rgba(1, 1, 1, 0) }
        GradientStop { position: 0.5; color: Qt.rgba(1, 1, 1, reflejo.fuerza) }
        GradientStop { position: 1; color: Qt.rgba(1, 1, 1, 0) }
    }
}
