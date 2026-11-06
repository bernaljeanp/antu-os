// Mantiene visible el control al que se llega con Tab, incluso con texto ampliado.
import QtQuick
import QtQuick.Window

Flickable {
    id: scroll
    clip: true
    property bool onlyKeyboardFocus: false
    Connections {
        target: scroll.Window.window
        function onActiveFocusItemChanged() {
            const targetFocus = scroll.Window.window ? scroll.Window.window.activeFocusItem : null
            if (scroll.onlyKeyboardFocus) {
                let control = targetFocus
                while (control && control !== scroll.contentItem && control.focusReason === undefined)
                    control = control.parent
                if (!control || (control.focusReason !== Qt.TabFocusReason && control.focusReason !== Qt.BacktabFocusReason)) return
            }
            Qt.callLater(function() {
                const ventana = scroll.Window.window
                const foco = ventana ? ventana.activeFocusItem : null
                if (!foco || foco !== targetFocus) return
                let padre = foco
                while (padre && padre !== scroll.contentItem) padre = padre.parent
                if (!padre) return
                const punto = foco.mapToItem(scroll.contentItem, 0, 0)
                let destino = scroll.contentY
                if (punto.y < destino + 12) destino = punto.y - 12
                else if (punto.y + foco.height > destino + scroll.height - 12)
                    destino = punto.y + foco.height - scroll.height + 12
                scroll.contentY = Math.max(0, Math.min(destino, scroll.contentHeight - scroll.height))
            })
        }
    }
}
