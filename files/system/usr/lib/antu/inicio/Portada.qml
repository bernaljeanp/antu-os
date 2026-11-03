// Portada de un juego con esquinas de verdad: la imagen se recorta a la forma de lo que la contiene. Con fundida, la parte de abajo
// se desvanece en lo que hay detrás, sin línea de corte. Sin imagen, la inicial del juego sobre vidrio.
import QtQuick
import QtQuick.Effects

Item {
    id: portada

    property real u: 1
    property string imagen
    property string nombre
    property real radio: 16
    property bool fundida: false
    readonly property bool lista: foto.status === Image.Ready
    readonly property bool porSoftware: GraphicsInfo.api === GraphicsInfo.Software

    Rectangle {
        anchors.fill: parent
        visible: !portada.lista
        radius: portada.radio
        color: Qt.rgba(1, 1, 1, 0.05)
        Text {
            anchors.centerIn: parent
            text: portada.nombre.charAt(0)
            textFormat: Text.PlainText
            color: Qt.rgba(1, 1, 1, 0.16)
            font.family: "Inter"
            font.pixelSize: Math.min(parent.height * 0.5, 96 * portada.u)
            font.weight: Font.Bold
        }
    }
    Image {
        id: foto
        anchors.fill: parent
        source: portada.imagen
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        visible: portada.porSoftware  // sin aceleración (capturas de CI) no hay recorte: mejor cuadrada que invisible
    }
    Item {  // la forma del recorte
        id: forma
        anchors.fill: parent
        visible: false
        layer.enabled: true
        clip: true
        Rectangle {
            width: parent.width
            height: parent.height + (portada.fundida ? portada.radio : 0)
            radius: portada.radio
            antialiasing: true
            gradient: Gradient {
                GradientStop { position: 0; color: "#000000" }
                GradientStop { position: portada.fundida ? 0.62 : 1; color: "#000000" }
                GradientStop { position: 1; color: portada.fundida ? "transparent" : "#000000" }
            }
        }
    }
    MultiEffect {
        anchors.fill: parent
        visible: portada.lista && !portada.porSoftware
        source: foto
        maskEnabled: true
        maskSource: forma
        maskThresholdMin: 0.5
        maskSpreadAtMin: 1
    }
}
