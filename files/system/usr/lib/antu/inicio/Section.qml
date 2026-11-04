// Sección plegable de Inicio: abierta muestra sus controles; cerrada muestra su estado y un resumen de una línea.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: section

    property string title
    property string summary
    property bool done: false
    property bool open: false
    property real u: 1
    default property alias content: body.data
    signal headerClicked()

    Layout.fillWidth: true
    implicitHeight: column.implicitHeight + 56 * u
    clip: true
    radius: 18 * u
    color: Qt.rgba(1, 1, 1, open ? 0.10 : (header.hovered ? 0.08 : 0.06))
    border.width: 1
    border.color: Qt.rgba(1, 1, 1, open ? 0.22 : 0.14)

    // El único movimiento de Inicio: abrir y plegar secciones.
    Behavior on implicitHeight { NumberAnimation { duration: Antu.duration(240); easing.type: Easing.OutCubic } }
    Behavior on color { ColorAnimation { duration: Antu.duration(160) } }

    ColumnLayout {
        id: column
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 28 * section.u
        spacing: 22 * section.u

        AbstractButton {
            id: header
            Layout.fillWidth: true
            implicitHeight: Math.max(48 * section.u, rotulo.implicitHeight + 16 * section.u)
            Accessible.name: section.title + (section.done ? ", completado" : "")
            onClicked: section.headerClicked()
            background: Rectangle {
                color: "transparent"
                radius: 12 * section.u
                border.width: header.visualFocus ? 2 * section.u : 0
                border.color: "#FF5A1F"
            }
            contentItem: RowLayout {
                spacing: 18 * section.u
                Rectangle {
                    implicitWidth: 32 * section.u
                    implicitHeight: implicitWidth
                    radius: width / 2
                    color: section.done ? "#FF5A1F" : "transparent"
                    border.width: section.done ? 0 : 2 * section.u
                    border.color: section.open ? "#FF5A1F" : Qt.rgba(1, 1, 1, 0.38)
                    Image {
                        anchors.centerIn: parent
                        visible: section.done
                        source: "check.svg"
                        sourceSize.width: 18 * section.u
                        sourceSize.height: 18 * section.u
                    }
                }
                Text {
                    id: rotulo
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    wrapMode: Text.WordWrap
                    text: section.title
                    color: Antu.ink
                    font.family: "Inter"
                    font.pixelSize: Antu.pixels(28, section.u)
                    font.weight: Font.DemiBold
                }
                Item { Layout.fillWidth: true }
                Text {
                    visible: !section.open && section.summary.length > 0
                    Layout.maximumWidth: 460 * section.u
                    text: section.summary
                    color: Antu.secondary
                    elide: Text.ElideRight
                    font.family: "Inter"
                    font.pixelSize: Antu.pixels(22, section.u)
                }
            }
        }

        ColumnLayout {
            id: body
            visible: section.open
            Layout.fillWidth: true
            Layout.leftMargin: section.width < 700 ? 0 : 50 * section.u
            spacing: 18 * section.u
        }
    }
}
