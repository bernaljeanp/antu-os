// Botón de Antu: material, no color plano. Lo principal es lava con luz propia; lo secundario, una tecla oscura retroiluminada
// como las del teclado de un portátil gamer; lo que borra, lava roja. Al apretarlo baja de verdad, y el foco se ve con teclado.
import QtQuick
import QtQuick.Controls.Basic

Button {
    id: button

    property real u: 1
    property bool primary: true
    property bool destructive: false

    readonly property bool tecla: !primary && !destructive
    readonly property color luz: destructive ? "#D1301F" : (primary ? "#FF5A1F" : "#FFC9A8")
    readonly property color claro: destructive ? "#EC6657" : "#F97A3C"
    readonly property color medio: destructive ? "#C42B1C" : "#E2480F"
    readonly property color oscuro: destructive ? "#8F1C10" : "#B93A0A"
    readonly property real radio: 16 * u
    property real recorrido: down && enabled ? (tecla ? 4 : 2) * u : 0

    Behavior on recorrido { NumberAnimation { duration: 70; easing.type: Easing.OutCubic } }

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
        style: button.enabled ? Text.Raised : Text.Normal
        styleColor: button.tecla ? Qt.rgba(1, 0.79, 0.66, 0.3) : Qt.rgba(0.3, 0.06, 0, 0.8)
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        transform: Translate { y: button.recorrido }
    }
    background: Item {
        Halo {  // su sombra sobre lo que hay debajo
            anchors.fill: parent
            radio: button.radio
            alcance: (button.down ? 6 : 14) * button.u
            fuerza: button.enabled ? 0.42 : 0
            bajada: (button.down ? 2 : 8) * button.u
        }
        Halo {  // la luz que da
            anchors.fill: parent
            radio: button.radio
            tono: button.luz
            alcance: (button.hovered ? 26 : 16) * button.u
            fuerza: !button.enabled ? 0
                  : button.tecla ? (button.hovered || button.down ? 0.26 : 0.1)
                  : (button.hovered ? 0.42 : (button.down ? 0.12 : 0.22))
            bajada: 8 * button.u
        }
        Rectangle {  // la tecla: la luz se escapa por la ranura de abajo
            visible: button.tecla && button.enabled
            anchors.fill: parent
            anchors.topMargin: 8 * button.u
            anchors.bottomMargin: -5 * button.u
            radius: button.radio
            color: Qt.rgba(button.luz.r, button.luz.g, button.luz.b, button.hovered || button.down ? 0.55 : 0.28)
        }
        Rectangle {  // el canto: claro arriba, oscuro abajo
            y: button.recorrido
            width: parent.width
            height: parent.height
            radius: button.radio
            gradient: Gradient {
                GradientStop {
                    position: 0
                    color: !button.enabled ? "#34343A" : (button.tecla ? "#5C5C66" : Qt.lighter(button.claro, 1.28))
                }
                GradientStop {
                    position: button.tecla ? 0.2 : 0.45
                    color: !button.enabled ? "#26262B" : (button.tecla ? "#2C2C33" : button.medio)
                }
                GradientStop {
                    position: 1
                    color: !button.enabled ? "#1B1B1F" : (button.tecla ? "#0C0C0F" : Qt.darker(button.oscuro, 1.5))
                }
            }
            Rectangle {  // la cara
                anchors.fill: parent
                anchors.margins: 1
                anchors.bottomMargin: button.tecla ? 3 * button.u : 1
                radius: button.radio - 1
                clip: true
                gradient: Gradient {
                    GradientStop {
                        position: 0
                        color: !button.enabled ? "#2B2B30" : button.tecla ? (button.hovered ? "#3A3A42" : "#33333A")
                             : button.down ? button.medio : (button.hovered ? Qt.lighter(button.claro, 1.08) : button.claro)
                    }
                    GradientStop {
                        position: 0.55
                        color: !button.enabled ? "#232327" : button.tecla ? (button.hovered ? "#2D2D34" : "#27272D")
                             : button.down ? button.oscuro : button.medio
                    }
                    GradientStop {
                        position: 1
                        color: !button.enabled ? "#1E1E22" : button.tecla ? (button.hovered ? "#24242A" : "#1C1C21") : button.oscuro
                    }
                }
                Rectangle {  // lava: calor que sube desde abajo
                    visible: !button.tecla && button.enabled
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: parent.height * 0.5
                    radius: parent.radius
                    gradient: Gradient {
                        GradientStop { position: 0; color: Qt.rgba(1, 0.75, 0.45, 0) }
                        GradientStop { position: 1; color: Qt.rgba(1, 0.75, 0.45, button.down ? 0.05 : 0.18) }
                    }
                }
                Reflejo {
                    visible: button.enabled
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.margins: 10 * button.u
                    y: 1
                    fuerza: button.tecla ? 0.34 : (button.down ? 0.1 : 0.6)
                }
            }
        }
        Rectangle {  // foco con teclado
            visible: button.visualFocus
            y: button.recorrido - 4 * button.u
            x: -4 * button.u
            width: parent.width + 8 * button.u
            height: parent.height + 8 * button.u
            radius: button.radio + 4 * button.u
            color: "transparent"
            border.width: 2.5 * button.u
            border.color: "#FFFFFF"
        }
    }
}
