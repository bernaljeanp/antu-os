import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "../inicio"

ApplicationWindow {
    id: root
    width: 1100
    height: 760
    minimumWidth: 760
    minimumHeight: 600
    visible: true
    title: "Antu en vivo"
    color: Antu.base
    property string errorTexto: ""
    Connections { target: backend; function onError(texto) { root.errorTexto = texto } }
    AntuBackdrop { anchors.fill: parent; photographic: true; shade: 0.72 }
    FocusScroll {
        anchors.fill: parent
        contentHeight: contenido.implicitHeight + 96
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { }
        ColumnLayout {
            id: contenido
            width: Math.min(760, parent.width - 80)
            anchors.horizontalCenter: parent.horizontalCenter
            y: 48
            spacing: 18
            Image { source: Antu.symbolSource; sourceSize.width: 64; sourceSize.height: 64; Layout.bottomMargin: 8 }
            Text {
                Layout.fillWidth: true
                text: "Prueba Antu sin instalar"
                wrapMode: Text.WordWrap
                color: Antu.ink
                font.family: "Inter"
                font.pixelSize: Antu.pixels(36)
                font.weight: Font.Bold
            }
            Text {
                Layout.fillWidth: true
                text: "Ya estás usando Antu desde el USB. Puedes explorar el escritorio, conectar tus dispositivos y probar un juego."
                wrapMode: Text.WordWrap
                color: Antu.secondary
                font.family: "Inter"
                font.pixelSize: Antu.pixels(18)
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.topMargin: 12
                implicitHeight: opciones.implicitHeight + 48
                radius: 16
                color: Antu.window
                border.width: 1
                border.color: Antu.softEdge
                ColumnLayout {
                    id: opciones
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 24
                    spacing: 16
                    LavaButton { text: "Probar Antu"; u: 0.78; focus: true; onClicked: root.close() }
                    Text {
                        Layout.fillWidth: true
                        text: "Tus discos siguen como están. Al apagar se descarta lo que hayas cambiado en esta sesión, salvo los informes guardados en el USB."
                        wrapMode: Text.WordWrap
                        color: Antu.secondary
                        font.family: "Inter"
                        font.pixelSize: Antu.pixels(16)
                    }
                    Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: Antu.softEdge; Layout.topMargin: 6; Layout.bottomMargin: 6 }
                    LavaButton { text: "Instalar Antu…"; primary: false; u: 0.78; onClicked: backend.abrir("instalar") }
                    Text {
                        Layout.fillWidth: true
                        text: "El instalador te mostrará los discos y te pedirá confirmar qué se borrará antes de hacer cambios."
                        wrapMode: Text.WordWrap
                        color: Antu.secondary
                        font.family: "Inter"
                        font.pixelSize: Antu.pixels(16)
                    }
                }
            }
            Text {
                Layout.fillWidth: true
                text: backend.registro
                wrapMode: Text.WordWrap
                color: Antu.secondary
                font.family: "Inter"
                font.pixelSize: Antu.pixels(14)
            }
            LavaButton { text: "Informe del equipo"; primary: false; u: 0.66; onClicked: backend.abrir("informe") }
            Text {
                visible: root.errorTexto.length > 0
                Layout.fillWidth: true
                text: root.errorTexto
                wrapMode: Text.WordWrap
                color: Antu.negative
                font.family: "Inter"
                font.pixelSize: Antu.pixels(16)
                Accessible.role: Accessible.AlertMessage
            }
        }
    }
}
