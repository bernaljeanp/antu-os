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
    readonly property color claro: destructive ? "#BA382B" : "#C44317"
    readonly property color medio: destructive ? "#A52A1D" : "#B3340D"
    readonly property color oscuro: destructive ? "#801C12" : "#922909"
    readonly property real radio: 16 * u
    property real recorrido: down && enabled ? (tecla ? 4 : 2) * u : 0

    Behavior on recorrido { enabled: Antu.motionFactor > 0; NumberAnimation { duration: Antu.duration(70); easing.type: Easing.OutCubic } }

    implicitHeight: Math.max(40, 60 * u, font.pixelSize * 1.5 + 12)
    leftPadding: 34 * u
    rightPadding: 34 * u
    font.family: "Inter"
    font.pixelSize: Antu.pixels(23, u)
    font.weight: Font.DemiBold
    contentItem: Text {
        text: button.text
        font: button.font
        color: !button.enabled ? Antu.muted : button.tecla ? Antu.ink : "#FFFFFF"
        style: Text.Normal
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
            fuerza: button.enabled ? (Antu.dark ? 0.32 : 0.13) : 0
            bajada: (button.down ? 2 : 8) * button.u
        }
        Halo {  // la luz que da
            anchors.fill: parent
            radio: button.radio
            tono: button.luz
            alcance: (button.hovered ? 26 : 16) * button.u
            fuerza: !button.enabled ? 0
                  : button.tecla ? (button.hovered || button.down ? 0.12 : 0.04)
                  : (button.hovered ? 0.22 : (button.down ? 0.08 : 0.12))
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
                    color: !button.enabled ? Antu.softEdge : (button.tecla ? Antu.edge : Qt.lighter(button.claro, 1.28))
                }
                GradientStop {
                    position: button.tecla ? 0.2 : 0.45
                    color: !button.enabled ? Antu.raised : (button.tecla ? Antu.raised : button.medio)
                }
                GradientStop {
                    position: 1
                    color: !button.enabled ? Antu.window : (button.tecla ? Antu.window : Qt.darker(button.oscuro, 1.3))
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
                        color: !button.enabled ? Antu.raised : button.tecla ? (button.hovered ? Antu.raisedHover : Antu.raised)
                             : button.down ? button.medio : button.claro
                    }
                    GradientStop {
                        position: 0.55
                        color: !button.enabled ? Antu.window : button.tecla ? (button.hovered ? Antu.raisedHover : Antu.raised)
                             : button.down ? button.oscuro : button.medio
                    }
                    GradientStop {
                        position: 1
                        color: !button.enabled ? Antu.window : button.tecla ? Antu.window : button.oscuro
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
                        GradientStop { position: 1; color: Qt.rgba(1, 0.75, 0.45, button.down ? 0.02 : 0.04) }
                    }
                }
                Reflejo {
                    visible: button.enabled
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.margins: 10 * button.u
                    y: 1
                    fuerza: button.tecla ? 0.18 : (button.down ? 0.08 : 0.32)
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
            border.color: Antu.dark ? "#FFFFFF" : "#25252C"
        }
    }
}
