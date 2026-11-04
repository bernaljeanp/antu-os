// La ventana de aviso.py: la placa flotando sobre el escritorio, sin marco, con espacio para su sombra.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Window
import "../inicio"

Window {
    id: ventana

    readonly property real margen: 48

    width: Math.min(Screen.width - 48, 760 * Antu.textFactor)
    height: Math.min(Screen.height - 80, placa.implicitHeight + 2 * margen)
    visible: true
    color: "transparent"
    flags: Qt.Dialog | Qt.FramelessWindowHint
    title: backend.titulo

    onClosing: backend.salir(1)  // cerrarla sin elegir es lo mismo que no aceptar

    Shortcut {
        sequence: "Escape"
        onActivated: backend.salir(1)
    }

    FocusScroll {
        anchors.fill: parent
        anchors.margins: ventana.margen
        contentHeight: placa.implicitHeight
        contentWidth: width
        ScrollBar.vertical: ScrollBar { }
    Aviso {
        id: placa
        width: parent.width
        titulo: backend.titulo
        texto: backend.texto
        tipo: backend.tipo
        LavaButton {
            text: backend.aceptar
            focus: true
            Keys.onReturnPressed: backend.salir(0)
            Keys.onEnterPressed: backend.salir(0)
            onClicked: backend.salir(0)
        }
        LavaButton {
            visible: backend.cancelar.length > 0
            primary: false
            text: backend.cancelar
            onClicked: backend.salir(1)
        }
    }
    }
}
