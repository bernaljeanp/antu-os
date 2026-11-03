// Sombra o luz difusa: capas apiladas, sin efectos que dependan de la gráfica (se ve igual en una máquina virtual).
import QtQuick

Item {
    id: halo

    property real radio: 16
    property color tono: "#000000"
    property real alcance: 16
    property real fuerza: 0.3
    property real bajada: 6

    Behavior on fuerza { NumberAnimation { duration: 120 } }
    Behavior on alcance { NumberAnimation { duration: 120 } }

    Repeater {
        model: 10
        Rectangle {
            required property int index
            readonly property real extra: (index + 1) / 10 * halo.alcance
            x: -extra
            y: -extra + halo.bajada
            width: halo.width + 2 * extra
            height: halo.height + 2 * extra
            radius: halo.radio + extra
            color: Qt.rgba(halo.tono.r, halo.tono.g, halo.tono.b, halo.fuerza / 10)
        }
    }
}
