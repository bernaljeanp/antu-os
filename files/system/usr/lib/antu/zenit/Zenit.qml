// Zenit en Antu: tablero de instrumentos del equipo. Temperaturas y perfil arriba, luego refrigeración, luces,
// batería y perfil por juego. Mismo mundo visual que Inicio y el instalador: vidrio de obsidiana y lava.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "../inicio"

ApplicationWindow {
    id: root
    width: 1280
    height: 880
    minimumWidth: 980
    minimumHeight: 680
    visible: false
    title: "Zenit"
    color: "#0B0B0E"

    readonly property real u: 0.62
    readonly property color ink: "#F5F5F7"
    readonly property color ink2: "#C7C7CC"
    readonly property color ink3: "#8E8E93"
    readonly property color lava: "#FF5A1F"

    readonly property var e: backend.estado
    readonly property bool conectado: backend.conectado
    readonly property var temps: e.temperaturas || ({})
    readonly property var fans: e.ventiladores || ({})
    readonly property int cpu: temps.CPU !== undefined ? temps.CPU : (Object.keys(temps).length ? temps[Object.keys(temps)[0]] : 0)
    readonly property int gpu: temps.GPU !== undefined ? temps.GPU : 0
    readonly property bool auto: e.modo === "auto"
    readonly property var perfiles: e.perfiles || []
    property var historia: backend.historiaInicial
    property string avisoTexto: ""

    function nombrePerfil(id) { return backend.nombresPerfil[id] || id || "sin perfil" }
    function miles(n) { return Number(n).toLocaleString(Qt.locale("es_CL"), "f", 0) }

    // Cerrar la ventana la deja junto al reloj; el servicio y el ícono siguen.
    onClosing: (close) => { close.accepted = false; root.hide() }

    Connections {
        target: backend
        function onCambio() {
            if (!root.conectado) return
            const h = root.historia.slice(-59)
            h.push(root.cpu)
            root.historia = h
        }
        function onAviso(texto) {
            root.avisoTexto = texto
            avisoReloj.restart()
        }
    }

    // ---------- Piezas ----------

    component Panel: Rectangle {
        property string titulo
        default property alias contenido: cuerpo.data
        Layout.fillWidth: true
        implicitHeight: columna.implicitHeight + 64 * root.u
        radius: 22 * root.u
        color: Qt.rgba(1, 1, 1, 0.045)
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.10)
        ColumnLayout {
            id: columna
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 32 * root.u
            spacing: 22 * root.u
            Text {
                visible: text.length > 0
                text: titulo
                color: root.ink
                font.family: "Inter"
                font.pixelSize: 30 * root.u
                font.weight: Font.DemiBold
            }
            ColumnLayout {
                id: cuerpo
                Layout.fillWidth: true
                spacing: 18 * root.u
            }
        }
    }

    component Nota: Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        color: root.ink2
        font.family: "Inter"
        font.pixelSize: 22 * root.u
        lineHeight: 1.15
    }

    // Dial de temperatura: arco de 270° que pasa de ámbar a lava y a rojo según el calor.
    component Dial: Item {
        id: dial
        property real valor: 0
        property string etiqueta
        property string pie
        property real mostrado: valor
        Behavior on mostrado { NumberAnimation { duration: 700; easing.type: Easing.OutCubic } }
        onMostradoChanged: lienzo.requestPaint()
        implicitWidth: 300 * root.u
        implicitHeight: 300 * root.u
        Canvas {
            id: lienzo
            anchors.fill: parent
            onPaint: {
                const c = getContext("2d")
                const r = width / 2 - 18 * root.u
                const ini = Math.PI * 0.75
                const fin = ini + Math.PI * 1.5 * Math.min(1, Math.max(0, (dial.mostrado - 30) / 75))
                c.reset()
                c.lineCap = "round"
                c.lineWidth = 16 * root.u
                c.strokeStyle = Qt.rgba(1, 1, 1, 0.08)
                c.beginPath(); c.arc(width / 2, height / 2, r, ini, Math.PI * 2.25); c.stroke()
                if (dial.mostrado <= 30) return
                const g = c.createLinearGradient(0, height, width, 0)
                g.addColorStop(0, "#FFB27A")
                g.addColorStop(0.6, root.lava)
                g.addColorStop(1, "#FF453A")
                c.strokeStyle = g
                c.beginPath(); c.arc(width / 2, height / 2, r, ini, fin); c.stroke()
                c.fillStyle = "#FFE3D3"
                c.beginPath()
                c.arc(width / 2 + r * Math.cos(fin), height / 2 + r * Math.sin(fin), 6 * root.u, 0, Math.PI * 2)
                c.fill()
            }
        }
        Column {
            anchors.centerIn: parent
            spacing: 4 * root.u
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: dial.valor > 0 ? Math.round(dial.mostrado) + "°" : "—"
                color: root.ink
                font.family: "Inter"
                font.pixelSize: 84 * root.u
                font.weight: Font.Bold
                font.features: ({ "tnum": 1 })
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: dial.etiqueta
                color: root.ink2
                font.family: "Inter"
                font.pixelSize: 22 * root.u
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: dial.pie.length > 0
                text: dial.pie
                color: root.ink3
                font.family: "Inter"
                font.pixelSize: 19 * root.u
                font.features: ({ "tnum": 1 })
            }
        }
    }

    component Chip: Rectangle {
        property string texto
        property bool encendido: false
        implicitWidth: chipTexto.implicitWidth + 36 * root.u
        implicitHeight: 40 * root.u
        radius: height / 2
        color: encendido ? Qt.rgba(1, 0.353, 0.122, 0.18) : Qt.rgba(1, 1, 1, 0.07)
        border.width: 1
        border.color: encendido ? Qt.rgba(1, 0.353, 0.122, 0.55) : Qt.rgba(1, 1, 1, 0.12)
        Text {
            id: chipTexto
            anchors.centerIn: parent
            text: parent.texto
            color: root.ink
            font.family: "Inter"
            font.pixelSize: 19 * root.u
            font.weight: Font.Medium
        }
    }

    // Opción elegible (perfil, límite de carga): resaltada en lava cuando está activa.
    component Opcion: AbstractButton {
        id: opcion
        property string titulo
        property string detalle
        property bool activa: false
        property bool tenue: false  // activa por el modo automático, no elegida a mano
        Layout.fillWidth: true
        implicitHeight: 96 * root.u
        Accessible.name: titulo + (activa ? ", activo" : "")
        background: Rectangle {
            radius: 16 * root.u
            color: opcion.activa && !opcion.tenue ? Qt.rgba(1, 0.353, 0.122, 0.20)
                 : opcion.hovered ? Qt.rgba(1, 1, 1, 0.09) : Qt.rgba(1, 1, 1, 0.04)
            border.width: opcion.activa || opcion.visualFocus ? 2 * root.u : 1
            border.color: opcion.activa || opcion.visualFocus ? root.lava : Qt.rgba(1, 1, 1, 0.10)
            Behavior on color { ColorAnimation { duration: 140 } }
        }
        contentItem: Column {
            spacing: 4 * root.u
            topPadding: 18 * root.u
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: opcion.titulo
                color: opcion.enabled ? root.ink : root.ink3
                font.family: "Inter"
                font.pixelSize: 23 * root.u
                font.weight: Font.DemiBold
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: opcion.detalle
                color: root.ink2
                font.family: "Inter"
                font.pixelSize: 18 * root.u
            }
        }
    }

    // ---------- Página ----------

    Flickable {
        id: pagina
        anchors.fill: parent
        contentHeight: contenido.implicitHeight + 120 * root.u
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        ColumnLayout {
            id: contenido
            width: Math.min(1900 * root.u, pagina.width - 96 * root.u)
            anchors.horizontalCenter: parent.horizontalCenter
            y: 56 * root.u
            spacing: 26 * root.u

            // Cabecera: marca y estado del servicio.
            RowLayout {
                Layout.bottomMargin: 8 * root.u
                spacing: 18 * root.u
                Image {
                    source: "file:///usr/share/icons/hicolor/256x256/apps/zenit.png"
                    sourceSize.width: 64 * root.u
                    sourceSize.height: 64 * root.u
                }
                ColumnLayout {
                    spacing: 2 * root.u
                    Text {
                        text: "Zenit"
                        color: root.ink
                        font.family: "Inter"
                        font.pixelSize: 44 * root.u
                        font.weight: Font.Bold
                    }
                    Text {
                        text: "Rendimiento, luces y batería de tu equipo"
                        color: root.ink2
                        font.family: "Inter"
                        font.pixelSize: 21 * root.u
                    }
                }
                Item { Layout.fillWidth: true }
                Chip {
                    texto: !root.conectado ? "Servicio sin respuesta"
                         : root.nombrePerfil(root.e.perfil) + (root.e.cargador ? " · con cargador" : " · con batería")
                    encendido: root.conectado
                }
            }

            // 1. Temperaturas y diagnóstico en palabras simples.
            Panel {
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 36 * root.u
                    Dial {
                        valor: root.cpu
                        etiqueta: "Procesador"
                        pie: root.fans.CPU !== undefined ? root.miles(root.fans.CPU) + " rpm" : ""
                    }
                    Dial {
                        valor: root.gpu
                        etiqueta: "Gráfica"
                        pie: root.fans.GPU !== undefined ? root.miles(root.fans.GPU) + " rpm" : ""
                    }
                    Rectangle {
                        Layout.fillHeight: true
                        Layout.topMargin: 30 * root.u
                        Layout.bottomMargin: 30 * root.u
                        implicitWidth: 1
                        color: Qt.rgba(1, 1, 1, 0.10)
                    }
                    ColumnLayout {
                        id: diagnostico
                        Layout.fillWidth: true
                        spacing: 14 * root.u
                        readonly property var mensaje:
                            !root.conectado ? ["El servicio Zenit no responde",
                                               "Los ajustes no se pueden cambiar por ahora. Reinicia el equipo; si sigue así, avísanos."]
                          : root.perfiles.length === 0 ? ["Este equipo no tiene control térmico compatible",
                                               "Zenit muestra lo que puede leer. Los perfiles funcionan en portátiles Alienware y en otros con perfil de energía en Linux."]
                          : root.e.boost ? ["Performance Boost activo", "Ventiladores y frecuencias al máximo. Pulsa F6 para volver."]
                          : root.e.sigilo ? ["Modo Sigilo", "Luces tenues y perfil Silencioso. Pulsa F7 para volver."]
                          : root.e.juego ? ["Jugando", root.e.juego + " corre en " + root.nombrePerfil(root.e.perfil) + ". Al cerrarlo vuelve tu perfil de siempre."]
                          : root.cpu >= 90 ? ["El procesador está muy caliente",
                                              "Revisa que las rejillas no estén tapadas, o elige un perfil con más ventilación."]
                          : ["Todo en orden", root.nombrePerfil(root.e.perfil) + (root.e.cargador ? " con el cargador." : " con batería.")
                                              + (root.auto ? " Zenit lo cambia solo al abrir un juego." : "")]
                        Text {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            text: diagnostico.mensaje[0]
                            color: root.ink
                            font.family: "Inter"
                            font.pixelSize: 40 * root.u
                            font.weight: Font.Bold
                        }
                        Nota { text: diagnostico.mensaje[1] }
                        Flow {
                            Layout.fillWidth: true
                            Layout.topMargin: 6 * root.u
                            spacing: 10 * root.u
                            visible: root.conectado
                            Chip { texto: root.auto ? "Automático" : "Perfil fijo"; encendido: root.auto }
                            Chip { texto: root.e.cargador ? "Con cargador" : "Con batería" }
                            Chip { texto: "Batería: " + (root.e.carga || "—") }
                        }
                    }
                }
            }

            // 2. Perfil térmico.
            Panel {
                titulo: "Perfil térmico"
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12 * root.u
                    Repeater {
                        model: [
                            { id: "quiet", detalle: "Ventiladores bajos" },
                            { id: "balanced", detalle: "Uso diario" },
                            { id: "balanced-performance", detalle: "Más potencia, poco ruido" },
                            { id: "performance", detalle: "Máximo, ventiladores arriba" }
                        ].filter(p => root.perfiles.length === 0 || root.perfiles.indexOf(p.id) >= 0)
                        delegate: Opcion {
                            required property var modelData
                            titulo: root.nombrePerfil(modelData.id)
                            detalle: modelData.detalle
                            enabled: root.perfiles.length > 0
                            activa: root.e.perfil === modelData.id
                            tenue: root.auto
                            onClicked: backend.perfil(modelData.id)
                        }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 18 * root.u
                    Switch {
                        checked: root.auto
                        enabled: root.perfiles.length > 0
                        text: "Automático"
                        font.family: "Inter"
                        font.pixelSize: 23 * root.u
                        palette.windowText: root.ink
                        palette.text: root.ink
                        palette.highlight: "#E2480F"
                        palette.mid: Qt.rgba(1, 1, 1, 0.3)
                        Accessible.name: "Perfil automático"
                        onToggled: backend.perfil(checked ? "auto" : (root.e.perfil || "balanced"))
                    }
                    Nota {
                        text: root.auto
                              ? "Equilibrado+ con el cargador, Equilibrado con batería y Rendimiento al abrir un juego de Steam, Heroic, Lutris o Bottles."
                              : "Perfil fijo: Zenit no lo cambia solo. Activa Automático para que se ajuste a lo que haces."
                    }
                }
            }

            // 3. Calor en el tiempo y refrigeración.
            RowLayout {
                Layout.fillWidth: true
                spacing: 26 * root.u
                Panel {
                    Layout.horizontalStretchFactor: 2
                    titulo: "Procesador, últimos 2 minutos"
                    Canvas {
                        Layout.fillWidth: true
                        implicitHeight: 230 * root.u
                        property var datos: root.historia
                        onDatosChanged: requestPaint()
                        onWidthChanged: requestPaint()
                        onPaint: {
                            const c = getContext("2d")
                            c.reset()
                            const y = t => height - (Math.min(105, Math.max(30, t)) - 30) / 75 * height
                            c.strokeStyle = Qt.rgba(1, 1, 1, 0.07)
                            c.lineWidth = 1
                            for (const t of [40, 60, 80]) { c.beginPath(); c.moveTo(0, y(t)); c.lineTo(width, y(t)); c.stroke() }
                            c.setLineDash([6, 6])
                            c.strokeStyle = Qt.rgba(1, 0.27, 0.23, 0.6)
                            c.beginPath(); c.moveTo(0, y(100)); c.lineTo(width, y(100)); c.stroke()
                            c.setLineDash([])
                            if (datos.length < 2) return
                            const paso = width / 59
                            const x0 = width - (datos.length - 1) * paso
                            const g = c.createLinearGradient(0, height, 0, 0)
                            g.addColorStop(0, "#FFB27A")
                            g.addColorStop(0.55, root.lava)
                            g.addColorStop(1, "#FF453A")
                            c.strokeStyle = g
                            c.lineWidth = 3
                            c.lineJoin = "round"
                            c.beginPath()
                            datos.forEach((t, i) => i ? c.lineTo(x0 + i * paso, y(t)) : c.moveTo(x0, y(t)))
                            c.stroke()
                        }
                    }
                    Nota {
                        text: "La línea punteada marca los 100 °C, donde el procesador empieza a frenarse solo para no calentarse más."
                        color: root.ink3
                        font.pixelSize: 19 * root.u
                    }
                }
                Panel {
                    Layout.horizontalStretchFactor: 1
                    Layout.alignment: Qt.AlignTop
                    titulo: "Refrigeración"
                    Repeater {
                        model: Object.keys(root.fans)
                        delegate: RowLayout {
                            id: filaVentilador
                            required property string modelData
                            readonly property int rpm: root.fans[modelData]
                            spacing: 18 * root.u
                            Image {
                                source: "ventilador.svg"
                                sourceSize.width: 56 * root.u
                                sourceSize.height: 56 * root.u
                                RotationAnimator on rotation {
                                    from: 0
                                    to: 360
                                    loops: Animation.Infinite
                                    duration: Math.max(600, 6000000 / Math.max(1, filaVentilador.rpm))
                                    running: root.visible && filaVentilador.rpm > 0
                                }
                            }
                            ColumnLayout {
                                spacing: 2 * root.u
                                Text {
                                    text: filaVentilador.modelData === "CPU" ? "Ventilador del procesador"
                                        : filaVentilador.modelData === "GPU" ? "Ventilador de la gráfica"
                                        : "Ventilador " + filaVentilador.modelData
                                    color: root.ink2
                                    font.family: "Inter"
                                    font.pixelSize: 20 * root.u
                                }
                                Text {
                                    text: root.miles(filaVentilador.rpm) + " rpm"
                                    color: root.ink
                                    font.family: "Inter"
                                    font.pixelSize: 30 * root.u
                                    font.weight: Font.DemiBold
                                    font.features: ({ "tnum": 1 })
                                }
                            }
                        }
                    }
                    Nota {
                        visible: Object.keys(root.fans).length === 0
                        text: "Este equipo no informa la velocidad de sus ventiladores."
                    }
                }
            }

            // 4. Luces y batería.
            RowLayout {
                Layout.fillWidth: true
                spacing: 26 * root.u
                Panel {
                    id: panelLuces
                    Layout.horizontalStretchFactor: 3
                    titulo: "Luces del teclado"
                    readonly property string tono: (root.e.luces || {}).color || "FFFFFF"
                    readonly property int brillo: (root.e.luces || {}).brillo !== undefined ? root.e.luces.brillo : 100
                    // Vista previa: un teclado que se ilumina con el color y el brillo elegidos.
                    Rectangle {
                        id: teclado
                        Layout.fillWidth: true
                        implicitHeight: 180 * root.u
                        radius: 18 * root.u
                        color: "#141418"
                        border.width: 1
                        border.color: Qt.rgba(1, 1, 1, 0.08)
                        property color auroraTono: "#19FF7A"
                        readonly property color luz: panelLuces.tono === "AURORA" ? auroraTono : "#" + panelLuces.tono
                        SequentialAnimation on auroraTono {
                            running: root.visible && panelLuces.tono === "AURORA"
                            loops: Animation.Infinite
                            ColorAnimation { to: "#00E0D0"; duration: 1800 }
                            ColorAnimation { to: "#1E7BFF"; duration: 1800 }
                            ColorAnimation { to: "#7A3CFF"; duration: 1800 }
                            ColorAnimation { to: "#D02BFF"; duration: 1800 }
                            ColorAnimation { to: "#19FF7A"; duration: 1800 }
                        }
                        Column {
                            anchors.centerIn: parent
                            spacing: 8 * root.u
                            Repeater {
                                model: [14, 14, 13, 12, 7]
                                delegate: Row {
                                    id: filaTeclas
                                    required property int modelData
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    spacing: 8 * root.u
                                    Repeater {
                                        model: filaTeclas.modelData
                                        delegate: Rectangle {
                                            required property int index
                                            width: (filaTeclas.modelData === 7 && index === 3 ? 230 : 40) * root.u
                                            height: 24 * root.u
                                            radius: 6 * root.u
                                            color: Qt.rgba(1, 1, 1, 0.05)
                                            border.width: 1
                                            border.color: Qt.rgba(1, 1, 1, 0.06)
                                            Rectangle {
                                                anchors.fill: parent
                                                anchors.margins: 1
                                                radius: parent.radius
                                                color: teclado.luz
                                                opacity: panelLuces.brillo / 100 * 0.55
                                                Behavior on opacity { NumberAnimation { duration: 250 } }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 14 * root.u
                        Repeater {
                            model: ["FF5A1F", "FFFFFF", "7CC4FF", "1E7BFF", "8A5CFF", "FF2D55", "FFB800", "30D158", "AURORA"]
                            delegate: AbstractButton {
                                id: muestra
                                required property string modelData
                                readonly property bool elegido: panelLuces.tono === modelData
                                width: 52 * root.u
                                height: 52 * root.u
                                Accessible.name: modelData === "AURORA" ? "Aurora" : "Color " + modelData
                                onClicked: backend.luces(modelData, Math.max(panelLuces.brillo, 40))
                                background: Rectangle {
                                    radius: width / 2
                                    color: muestra.modelData === "AURORA" ? "#1E7BFF" : "#" + muestra.modelData
                                    gradient: muestra.modelData === "AURORA" ? auroraGradiente : null
                                    border.width: muestra.elegido || muestra.visualFocus ? 3 * root.u : 1
                                    border.color: muestra.elegido || muestra.visualFocus ? root.ink : Qt.rgba(1, 1, 1, 0.2)
                                    Gradient {
                                        id: auroraGradiente
                                        GradientStop { position: 0.0; color: "#19FF7A" }
                                        GradientStop { position: 0.5; color: "#1E7BFF" }
                                        GradientStop { position: 1.0; color: "#D02BFF" }
                                    }
                                }
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 18 * root.u
                        Text {
                            text: "Brillo"
                            color: root.ink2
                            font.family: "Inter"
                            font.pixelSize: 21 * root.u
                        }
                        Slider {
                            id: brillo
                            Layout.fillWidth: true
                            from: 0
                            to: 100
                            stepSize: 10
                            value: panelLuces.brillo
                            Accessible.name: "Brillo de las luces"
                            onMoved: soltar.restart()
                            palette.dark: root.lava
                            palette.midlight: Qt.rgba(1, 1, 1, 0.18)
                            Timer {
                                id: soltar
                                interval: 250
                                onTriggered: backend.luces(panelLuces.tono, Math.round(brillo.value))
                            }
                        }
                        Text {
                            text: Math.round(brillo.value) === 0 ? "Apagadas" : Math.round(brillo.value) + " %"
                            color: root.ink
                            font.family: "Inter"
                            font.pixelSize: 21 * root.u
                            font.features: ({ "tnum": 1 })
                            Layout.preferredWidth: 110 * root.u
                        }
                    }
                }
                Panel {
                    id: panelBateria
                    Layout.horizontalStretchFactor: 2
                    Layout.alignment: Qt.AlignTop
                    titulo: "Batería"
                    readonly property bool disponible: (root.e.carga_modo || "") !== ""
                    readonly property string actual: root.e.carga_modo === "Custom" ? String(root.e.carga_tope) : "adaptativa"
                    Repeater {
                        model: [
                            { id: "adaptativa", titulo: "Adaptativa", detalle: "El equipo decide según cómo lo usas" },
                            { id: "80", titulo: "Hasta 80 %", detalle: "Si casi siempre está enchufado" },
                            { id: "60", titulo: "Hasta 60 %", detalle: "Si vive en el escritorio" },
                            { id: "100", titulo: "Carga completa", detalle: "Para viajar o jugar sin cargador" }
                        ]
                        delegate: Opcion {
                            required property var modelData
                            implicitHeight: 84 * root.u
                            titulo: modelData.titulo
                            detalle: modelData.detalle
                            enabled: panelBateria.disponible
                            activa: enabled && panelBateria.actual === modelData.id
                            onClicked: backend.carga(modelData.id)
                        }
                    }
                    Nota {
                        text: panelBateria.disponible
                              ? "Se guarda en la BIOS: vale aunque Zenit no esté abierto. Cargar menos desgasta menos la batería."
                              : "Este equipo no permite fijar el límite de carga desde Linux."
                        color: root.ink3
                        font.pixelSize: 19 * root.u
                    }
                }
            }

            // 5. Perfil por juego.
            Panel {
                id: panelJuegos
                titulo: "Perfil por juego"
                readonly property var lista: {
                    const steam = backend.juegosSteam()
                    const otros = Object.keys(root.e.juegos || {}).filter(j => !steam.some(s => s.toLowerCase() === j))
                    return steam.concat(otros)
                }
                Repeater {
                    model: panelJuegos.lista
                    delegate: RowLayout {
                        id: filaJuego
                        required property string modelData
                        readonly property string clave: modelData.toLowerCase()
                        Layout.fillWidth: true
                        spacing: 16 * root.u
                        Text {
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            text: filaJuego.modelData
                            color: root.ink
                            font.family: "Inter"
                            font.pixelSize: 23 * root.u
                            font.weight: Font.Medium
                        }
                        Chip {
                            visible: root.e.juego === filaJuego.clave
                            texto: "Jugando ahora"
                            encendido: true
                        }
                        GlassCombo {
                            u: root.u
                            Layout.preferredWidth: 360 * root.u
                            textRole: "text"
                            valueRole: "value"
                            Accessible.name: "Perfil para " + filaJuego.modelData
                            model: [
                                { text: "Automático", value: "auto" },
                                { text: "Rendimiento", value: "performance" },
                                { text: "Equilibrado+", value: "balanced-performance" },
                                { text: "Equilibrado", value: "balanced" },
                                { text: "Silencioso", value: "quiet" }
                            ]
                            currentIndex: Math.max(0, indexOfValue((root.e.juegos || {})[filaJuego.clave] || "auto"))
                            onActivated: backend.juego(filaJuego.clave, currentValue)
                        }
                    }
                }
                Nota {
                    visible: panelJuegos.lista.length === 0
                    text: "Aún no hay juegos. Los de Steam aparecen solos; los de Heroic, Lutris o Bottles, la primera vez que los juegues."
                }
            }
        }
    }

    // Aviso flotante: por qué algo no se pudo hacer.
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 36 * root.u
        visible: opacity > 0
        opacity: root.avisoTexto.length > 0 ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 200 } }
        width: Math.min(avisoEtiqueta.implicitWidth + 56 * root.u, root.width - 80 * root.u)
        height: avisoEtiqueta.implicitHeight + 32 * root.u
        radius: height / 2
        color: "#2A1714"
        border.width: 1
        border.color: Qt.rgba(1, 0.44, 0.41, 0.6)
        Text {
            id: avisoEtiqueta
            anchors.centerIn: parent
            width: Math.min(implicitWidth, root.width - 136 * root.u)
            wrapMode: Text.WordWrap
            text: root.avisoTexto
            color: root.ink
            font.family: "Inter"
            font.pixelSize: 21 * root.u
        }
        Timer {
            id: avisoReloj
            interval: 6000
            onTriggered: root.avisoTexto = ""
        }
    }
}
