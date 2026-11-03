// Antu OS, Observatorio: cómo rinde cada juego a lo largo del tiempo y si una actualización lo empeoró. La pieza central es la
// carta de cada juego: una línea por sesión, con la fecha de cada actualización marcada sobre ella.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "../inicio"

ApplicationWindow {
    id: root
    width: 1280
    height: 820
    minimumWidth: 960
    minimumHeight: 640
    visible: true
    title: "Observatorio"
    color: "#0B0B0E"

    readonly property real u: Math.min(width / 1760, height / 1216)
    readonly property color ink: "#F5F5F7"
    readonly property color ink2: "#C7C7CC"
    readonly property color ink3: "#A1A1A6"
    readonly property color lava: "#FF5A1F"
    readonly property color superficie: "#17171C"

    property var juegos: []
    property int elegido: 0
    readonly property var juego: juegos.length > 0 ? juegos[elegido] : null
    readonly property bool hayFotogramas: !!juego && juego.sesiones.some(s => s.fps > 0)
    property bool enTabla: false
    // 0 nada, 1 preparando, 2 listo, 3 error
    property int vuelta: 0
    property string errorVuelta: ""

    Component.onCompleted: juegos = JSON.parse(backend.juegos)

    function colorDe(estado) {
        return estado === "baja" ? "#FF7069" : estado === "sube" ? "#57D98B" : "#A1A1A6"
    }

    Connections {
        target: backend
        function onTerminado(error) {
            root.errorVuelta = error
            root.vuelta = error.length > 0 ? 3 : 2
        }
    }

    Image {
        anchors.fill: parent
        source: "file:///usr/share/wallpapers/Paranal/contents/images_dark/3840x2160.jpg"
        sourceSize.width: 1920
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
    }
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.66
    }

    component Linea: Text {
        Layout.fillWidth: true
        textFormat: Text.PlainText
        wrapMode: Text.WordWrap
        color: root.ink2
        font.family: "Inter"
        font.pixelSize: 22 * root.u
    }

    // Sin nada que mostrar todavía.
    ColumnLayout {
        anchors.centerIn: parent
        width: 900 * root.u
        visible: root.juegos.length === 0
        spacing: 16 * root.u
        Text {
            Layout.fillWidth: true
            text: "Aún no hay juegos medidos"
            color: root.ink
            font.family: "Inter"
            font.pixelSize: 44 * root.u
            font.weight: Font.Bold
        }
        Linea {
            text: "Juega un rato: Antu mide solo, desde afuera, sin tocar el juego. Aquí verás cómo rinde cada uno y si una actualización lo cambia."
        }
    }

    RowLayout {
        anchors.fill: parent
        visible: root.juegos.length > 0
        spacing: 0

        // La lista: el nombre, cuánto rinde y si cambió.
        ColumnLayout {
            Layout.fillWidth: false
            Layout.preferredWidth: 620 * root.u
            Layout.fillHeight: true
            Layout.margins: 40 * root.u
            spacing: 24 * root.u

            RowLayout {
                spacing: 18 * root.u
                Image {
                    source: "file:///usr/share/antu/antu-symbol.svg"
                    sourceSize.width: 54 * root.u
                    sourceSize.height: 54 * root.u
                }
                Text {
                    text: "Observatorio"
                    color: root.ink
                    font.family: "Inter"
                    font.pixelSize: 44 * root.u
                    font.weight: Font.Bold
                    font.variableAxes: ({ "opsz": 32 })
                }
            }

            ListView {
                id: lista
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: root.juegos
                currentIndex: root.elegido
                spacing: 6 * root.u
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: ScrollBar { }
                delegate: AbstractButton {
                    id: fila
                    required property var modelData
                    required property int index
                    readonly property bool activa: root.elegido === index
                    width: lista.width
                    height: 112 * root.u
                    Accessible.name: modelData.nombre + ": " + modelData.etiqueta
                    onClicked: {
                        root.elegido = index
                        root.vuelta = 0
                    }
                    contentItem: Item { }
                    background: Rectangle {
                        radius: 14 * root.u
                        color: fila.activa ? Qt.rgba(1, 1, 1, 0.13) : (fila.hovered ? Qt.rgba(1, 1, 1, 0.08) : "transparent")
                        border.width: fila.visualFocus ? 3 * root.u : 0
                        border.color: "#FFFFFF"
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 12 * root.u
                            spacing: 16 * root.u
                            Rectangle {
                                Layout.preferredWidth: 188 * root.u
                                Layout.preferredHeight: 88 * root.u
                                radius: 8 * root.u
                                color: Qt.rgba(1, 1, 1, 0.06)
                                clip: true
                                Text {
                                    anchors.centerIn: parent
                                    visible: portada.status !== Image.Ready
                                    text: fila.modelData.nombre.charAt(0)
                                    textFormat: Text.PlainText
                                    color: Qt.rgba(1, 1, 1, 0.2)
                                    font.family: "Inter"
                                    font.pixelSize: 44 * root.u
                                    font.weight: Font.Bold
                                }
                                Image {
                                    id: portada
                                    anchors.fill: parent
                                    source: fila.modelData.imagen
                                    fillMode: Image.PreserveAspectCrop
                                    asynchronous: true
                                }
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4 * root.u
                                Text {
                                    Layout.fillWidth: true
                                    text: fila.modelData.nombre
                                    textFormat: Text.PlainText
                                    elide: Text.ElideRight
                                    color: root.ink
                                    font.family: "Inter"
                                    font.pixelSize: 24 * root.u
                                    font.weight: Font.DemiBold
                                }
                                RowLayout {
                                    spacing: 9 * root.u
                                    Rectangle {
                                        implicitWidth: 11 * root.u
                                        implicitHeight: 11 * root.u
                                        radius: width / 2
                                        color: root.colorDe(fila.modelData.estado)
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: fila.modelData.etiqueta
                                        textFormat: Text.PlainText
                                        elide: Text.ElideRight
                                        color: root.ink2
                                        font.family: "Inter"
                                        font.pixelSize: 20 * root.u
                                    }
                                }
                            }
                            Text {
                                visible: fila.modelData.fps.length > 0
                                text: fila.modelData.fps + " fps"
                                color: root.ink
                                font.family: "Inter"
                                font.pixelSize: 22 * root.u
                                font.weight: Font.Medium
                                font.features: ({ "tnum": 1 })
                            }
                        }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: "Antu mide desde afuera, sin cargar nada dentro del juego. Todo se queda en este equipo."
                color: root.ink3
                font.family: "Inter"
                font.pixelSize: 18 * root.u
            }
        }

        // La carta del juego elegido.
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: root.superficie
            border.width: 1
            border.color: Qt.rgba(1, 1, 1, 0.14)

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 44 * root.u
                spacing: 16 * root.u

                Text {
                    Layout.fillWidth: true
                    text: root.juego ? root.juego.nombre : ""
                    textFormat: Text.PlainText
                    elide: Text.ElideRight
                    color: root.ink3
                    font.family: "Inter"
                    font.pixelSize: 24 * root.u
                    font.weight: Font.Medium
                }
                Text {
                    Layout.fillWidth: true
                    text: root.juego ? root.juego.titulo : ""
                    textFormat: Text.PlainText
                    wrapMode: Text.WordWrap
                    color: root.ink
                    font.family: "Inter"
                    font.pixelSize: 40 * root.u
                    font.weight: Font.Bold
                    font.variableAxes: ({ "opsz": 32 })
                }
                Linea {
                    visible: text.length > 0
                    text: root.juego ? root.juego.detalle : ""
                }

                // La carta, o sus mismos datos como tabla.
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.topMargin: 12 * root.u
                    Layout.minimumHeight: 240 * root.u

                    Canvas {
                        id: carta
                        anchors.fill: parent
                        visible: !root.enTabla && root.hayFotogramas
                        property var datos: root.juego
                        property int encima: -1
                        readonly property real izq: 66 * root.u
                        readonly property real der: 104 * root.u
                        readonly property real arriba: 56 * root.u
                        readonly property real abajo: 40 * root.u
                        readonly property real tope: {
                            let m = 0
                            if (datos)
                                for (const s of datos.sesiones)
                                    m = Math.max(m, s.fps)
                            return Math.max(20, Math.ceil(m * 1.1 / 20) * 20)
                        }
                        function posX(i) {
                            const n = datos.sesiones.length
                            return n < 2 ? izq + (width - izq - der) / 2 : izq + i * (width - izq - der) / (n - 1)
                        }
                        function posY(v) {
                            return arriba + (height - arriba - abajo) * (1 - v / tope)
                        }
                        onDatosChanged: requestPaint()
                        onEncimaChanged: requestPaint()
                        onWidthChanged: requestPaint()
                        onHeightChanged: requestPaint()
                        onPaint: {
                            const c = getContext("2d")
                            c.reset()
                            if (!datos)
                                return
                            const fuente = Math.round(19 * root.u) + "px Inter"
                            const fuerte = "600 " + Math.round(22 * root.u) + "px Inter"
                            c.textBaseline = "middle"

                            // Eje: una línea tenue por cada 20 fotogramas, siempre desde cero.
                            const paso = tope > 120 ? (tope > 240 ? 80 : 40) : 20
                            c.font = fuente
                            c.textAlign = "right"
                            for (let v = 0; v <= tope; v += paso) {
                                c.strokeStyle = "rgba(255,255,255,0.09)"
                                c.lineWidth = 1
                                c.beginPath()
                                c.moveTo(izq, Math.round(posY(v)) + 0.5)
                                c.lineTo(width - der, Math.round(posY(v)) + 0.5)
                                c.stroke()
                                c.fillStyle = "#A1A1A6"
                                c.fillText(v, izq - 14 * root.u, posY(v))
                            }

                            // Cada actualización del sistema, donde empezó.
                            c.textAlign = "center"
                            for (let i = 1; i < datos.tramos.length; i++) {
                                const t = datos.tramos[i]
                                const raya = Math.round((posX(t.desde - 1) + posX(t.desde)) / 2) + 0.5
                                c.strokeStyle = "rgba(255,255,255,0.42)"
                                c.lineWidth = 1
                                c.beginPath()
                                c.moveTo(raya, arriba - 8 * root.u)
                                c.lineTo(raya, height - abajo)
                                c.stroke()
                                c.fillStyle = "#C7C7CC"
                                c.fillText("Actualización del " + t.fecha, raya, arriba - 28 * root.u)
                            }

                            // El nivel de cada versión, con su valor: es lo que cuenta la historia.
                            for (const t of datos.tramos) {
                                if (t.fps <= 0)
                                    continue
                                const a = posX(t.desde) - (t.desde === t.hasta ? 18 * root.u : 0)
                                const b = posX(t.hasta) + (t.desde === t.hasta ? 18 * root.u : 0)
                                c.strokeStyle = "rgba(245,245,247,0.55)"
                                c.lineWidth = 1
                                c.beginPath()
                                c.moveTo(a, Math.round(posY(t.fps)) + 0.5)
                                c.lineTo(b, Math.round(posY(t.fps)) + 0.5)
                                c.stroke()
                            }

                            // Las sesiones: cada una un punto; sin fotogramas medidos, no hay punto.
                            c.strokeStyle = "#FF5A1F"
                            c.lineWidth = 2
                            c.lineJoin = "round"
                            c.lineCap = "round"
                            c.beginPath()
                            let abierto = false
                            for (let i = 0; i < datos.sesiones.length; i++) {
                                const s = datos.sesiones[i]
                                if (s.fps <= 0) {
                                    abierto = false
                                    continue
                                }
                                if (abierto)
                                    c.lineTo(posX(i), posY(s.fps))
                                else
                                    c.moveTo(posX(i), posY(s.fps))
                                abierto = true
                            }
                            c.stroke()
                            for (let i = 0; i < datos.sesiones.length; i++) {
                                const s = datos.sesiones[i]
                                if (s.fps <= 0)
                                    continue
                                const radio = (i === encima ? 7 : 4.5) * Math.max(1, root.u * 1.4)
                                c.fillStyle = root.superficie
                                c.beginPath()
                                c.arc(posX(i), posY(s.fps), radio + 2, 0, 2 * Math.PI)
                                c.fill()
                                c.fillStyle = "#FF5A1F"
                                c.beginPath()
                                c.arc(posX(i), posY(s.fps), radio, 0, 2 * Math.PI)
                                c.fill()
                            }

                            // El valor de cada nivel, al final de su tramo y solo ahí.
                            c.font = fuerte
                            c.textAlign = "left"
                            c.fillStyle = "#F5F5F7"
                            const ultimo = datos.tramos[datos.tramos.length - 1]
                            if (ultimo.fps > 0)
                                c.fillText(Math.round(ultimo.fps) + " fps", posX(ultimo.hasta) + 14 * root.u, posY(ultimo.fps))
                            c.textAlign = "center"
                            for (let i = 0; i < datos.tramos.length - 1; i++) {
                                const t = datos.tramos[i]
                                if (t.fps > 0)
                                    c.fillText(Math.round(t.fps) + " fps", (posX(t.desde) + posX(t.hasta)) / 2, posY(t.fps) - 30 * root.u)
                            }

                            // Primera y última fecha.
                            c.font = fuente
                            c.fillStyle = "#A1A1A6"
                            c.textAlign = "left"
                            c.fillText(datos.sesiones[0].fecha, izq, height - abajo + 22 * root.u)
                            c.textAlign = "right"
                            if (datos.sesiones.length > 1)
                                c.fillText(datos.sesiones[datos.sesiones.length - 1].fecha, width - der, height - abajo + 22 * root.u)
                        }

                        // Al pasar por encima: el detalle de la sesión más cercana.
                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            onPositionChanged: mouse => {
                                let mejor = -1, distancia = 1e9
                                if (carta.datos)
                                    for (let i = 0; i < carta.datos.sesiones.length; i++) {
                                        const d = Math.abs(carta.posX(i) - mouse.x)
                                        if (d < distancia) {
                                            distancia = d
                                            mejor = i
                                        }
                                    }
                                carta.encima = mejor
                            }
                            onExited: carta.encima = -1
                        }
                        Rectangle {
                            readonly property var sesion: carta.encima >= 0 && carta.datos ? carta.datos.sesiones[carta.encima] : null
                            visible: sesion !== null && sesion.fps > 0
                            x: sesion ? Math.min(carta.width - width, Math.max(0, carta.posX(carta.encima) - width / 2)) : 0
                            y: sesion ? Math.max(0, carta.posY(sesion.fps) - height - 18 * root.u) : 0
                            width: textoSesion.implicitWidth + 28 * root.u
                            height: textoSesion.implicitHeight + 20 * root.u
                            radius: 10 * root.u
                            color: "#26262D"
                            border.width: 1
                            border.color: Qt.rgba(1, 1, 1, 0.18)
                            Text {
                                id: textoSesion
                                anchors.centerIn: parent
                                text: parent.sesion ? parent.sesion.fecha + ": " + Math.round(parent.sesion.fps) + " fps, " + parent.sesion.minutos + " min" : ""
                                color: root.ink
                                font.family: "Inter"
                                font.pixelSize: 19 * root.u
                            }
                        }
                    }

                    ListView {
                        anchors.fill: parent
                        visible: root.enTabla || !root.hayFotogramas
                        clip: true
                        model: root.juego ? root.juego.sesiones.slice().reverse() : []
                        boundsBehavior: Flickable.StopAtBounds
                        ScrollBar.vertical: ScrollBar { }
                        header: Row {
                            spacing: 0
                            Repeater {
                                model: ["Fecha", "Fotogramas", "Peores", "Minutos", "Gráfica", "Energía"]
                                Text {
                                    required property string modelData
                                    width: 150 * root.u
                                    height: 36 * root.u
                                    text: modelData
                                    color: root.ink3
                                    font.family: "Inter"
                                    font.pixelSize: 19 * root.u
                                }
                            }
                        }
                        delegate: Row {
                            id: filaTabla
                            required property var modelData
                            spacing: 0
                            Repeater {
                                model: [filaTabla.modelData.fecha,
                                        filaTabla.modelData.fps > 0 ? Math.round(filaTabla.modelData.fps) + " fps" : "Sin medir",
                                        filaTabla.modelData.bajo > 0 ? Math.round(filaTabla.modelData.bajo) + " fps" : "Sin medir",
                                        filaTabla.modelData.minutos + " min",
                                        filaTabla.modelData.temp > 0 ? Math.round(filaTabla.modelData.temp) + " °C" : "Sin medir",
                                        filaTabla.modelData.energia]
                                Text {
                                    required property string modelData
                                    width: 150 * root.u
                                    height: 36 * root.u
                                    text: modelData
                                    textFormat: Text.PlainText
                                    color: root.ink2
                                    font.family: "Inter"
                                    font.pixelSize: 21 * root.u
                                    font.features: ({ "tnum": 1 })
                                }
                            }
                        }
                    }
                }

                // Por qué puede ser y qué más se vio.
                Repeater {
                    model: root.juego && root.juego.estado !== "baja" && root.juego.cambios.length > 0 ? root.juego.cambios.split("\n") : []
                    Linea {
                        required property string modelData
                        text: "Cambió: " + modelData
                        color: root.ink
                    }
                }
                Repeater {
                    model: root.juego && root.juego.notas.length > 0 ? root.juego.notas.split("\n") : []
                    Linea {
                        required property string modelData
                        text: modelData
                    }
                }
                Aviso {
                    Layout.fillWidth: true
                    Layout.topMargin: 8 * root.u
                    visible: !!root.juego && root.juego.estado === "baja"
                    u: root.u
                    tipo: root.vuelta === 3 ? "peligro" : (root.vuelta === 2 ? "bien" : "atencion")
                    titulo: root.vuelta === 2 ? "Listo: al reiniciar vuelves a la versión anterior"
                          : root.vuelta === 3 ? "No se pudo preparar la versión anterior"
                          : "Puedes volver a la versión anterior"
                    texto: root.vuelta === 2 ? "Tus archivos no cambian."
                         : root.vuelta === 3 ? root.errorVuelta
                         : (root.juego && root.juego.cambios.length > 0 ? "Cambió: " + root.juego.cambios.replace(/\n/g, ". ") + ". " : "")
                           + "También pudo cambiar por un ajuste del juego: revísalo antes de volver atrás."
                    LavaButton {
                        u: root.u
                        visible: root.vuelta !== 2
                        enabled: root.vuelta !== 1
                        text: root.vuelta === 1 ? "Preparando…" : "Volver atrás"
                        onClicked: {
                            root.vuelta = 1
                            backend.volver()
                        }
                    }
                    LavaButton {
                        u: root.u
                        primary: false
                        text: root.enTabla ? "Ver carta" : "Ver tabla"
                        onClicked: root.enTabla = !root.enTabla
                    }
                }
                LavaButton {
                    Layout.topMargin: 8 * root.u
                    u: root.u
                    primary: false
                    visible: root.hayFotogramas && !!root.juego && root.juego.estado !== "baja"
                    text: root.enTabla ? "Ver carta" : "Ver tabla"
                    onClicked: root.enTabla = !root.enTabla
                }
            }
        }
    }
}
