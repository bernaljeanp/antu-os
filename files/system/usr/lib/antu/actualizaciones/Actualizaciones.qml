// Actualizaciones de Antu: qué versión tienes, si hay una lista para el próximo arranque y volver a la anterior si
// algo falla. Mismo mundo visual que el instalador: el fondo de Antu oscurecido, vidrio de obsidiana y lava.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "../inicio"

ApplicationWindow {
    id: root
    width: 960
    height: 680
    minimumWidth: 760
    minimumHeight: 580
    visible: true
    title: "Actualizaciones de Antu"
    color: "#0B0B0E"

    readonly property real u: Math.min(width / 1540, height / 1090)
    readonly property color ink: "#F5F5F7"
    readonly property color ink2: "#C7C7CC"
    readonly property color ink3: "#8E8E93"
    readonly property color lava: "#FF5A1F"

    readonly property var e: backend.estado
    property bool confirmando: false
    property string avisoTexto: ""

    function fecha(ts) { return ts ? Qt.locale("es_CL").toString(new Date(ts), "d 'de' MMMM 'de' yyyy") : "" }

    // 0 revisando, 1 al día, 2 buscando, 3 lista para reiniciar, 4 sin estado
    readonly property int situacion: !backend.cargado ? 0 : !e.disponible ? 4 : e.buscando ? 2 : e.lista ? 3 : 1
    readonly property string titular: ["Revisando…", "Antu está al día", "Buscando actualizaciones…",
                                       "Actualización lista", "No se pudo leer el estado"][situacion]
    readonly property string detalle: [
        "",
        "Antu busca solo cada 6 horas. Si quieres, puedes buscar ahora.",
        "Se baja en segundo plano y sin molestar: puedes seguir jugando.",
        (e.fecha_lista ? "La versión del " + fecha(e.fecha_lista) : "La versión nueva")
            + " ya está en tu equipo. Se aplica al reiniciar; tus archivos y apps no cambian.",
        "Las actualizaciones automáticas siguen funcionando. Si esto se repite, reinicia el equipo."
    ][situacion]

    Connections {
        target: backend
        function onAviso(texto) {
            root.avisoTexto = texto
            avisoReloj.restart()
        }
    }

    // Fondo: el de Antu, oscurecido, como en el instalador.
    Image {
        anchors.fill: parent
        source: "file:///usr/share/wallpapers/Antu/contents/images_dark/3840x2160.jpg"
        sourceSize.width: 1920
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
    }
    Rectangle {
        anchors.fill: parent
        color: "#000000"
        opacity: 0.62
    }

    ColumnLayout {
        width: Math.min(1180 * root.u, root.width - 120 * root.u)
        anchors.horizontalCenter: parent.horizontalCenter
        y: 90 * root.u
        spacing: 0

        Image {
            Layout.bottomMargin: 30 * root.u
            source: "file:///usr/share/antu/antu-symbol.svg"
            sourceSize.width: 76 * root.u
            sourceSize.height: 76 * root.u
        }
        Text {
            text: "Actualizaciones de Antu"
            color: root.ink
            font.family: "Inter"
            font.pixelSize: 50 * root.u
            font.weight: Font.Bold
            font.variableAxes: ({ "opsz": 32 })
        }
        Text {
            Layout.topMargin: 10 * root.u
            Layout.bottomMargin: 40 * root.u
            text: (root.e.instalada ? "Tienes la versión del " + root.fecha(root.e.instalada) + " · " : "")
                  + "canal " + (root.e.canal || "estable")
            color: root.ink2
            font.family: "Inter"
            font.pixelSize: 25 * root.u
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: tarjeta.implicitHeight + 76 * root.u
            radius: 22 * root.u
            color: Qt.rgba(1, 1, 1, 0.07)
            border.width: 1
            border.color: Qt.rgba(1, 1, 1, 0.16)

            ColumnLayout {
                id: tarjeta
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 38 * root.u
                spacing: 20 * root.u

                RowLayout {
                    spacing: 22 * root.u
                    // Señal del estado: un visto de lava si está al día, un anillo que gira mientras busca, el ícono
                    // de descarga si hay una versión lista.
                    Item {
                        implicitWidth: 64 * root.u
                        implicitHeight: 64 * root.u
                        Rectangle {
                            anchors.fill: parent
                            visible: root.situacion === 1
                            radius: width / 2
                            color: root.lava
                            Image {
                                anchors.centerIn: parent
                                source: "../inicio/check.svg"
                                sourceSize.width: 32 * root.u
                                sourceSize.height: 32 * root.u
                            }
                        }
                        Canvas {
                            id: anillo
                            anchors.fill: parent
                            visible: root.situacion === 0 || root.situacion === 2
                            onPaint: {
                                const c = getContext("2d")
                                c.reset()
                                c.lineWidth = 6 * root.u
                                c.lineCap = "round"
                                c.strokeStyle = Qt.rgba(1, 1, 1, 0.12)
                                c.beginPath(); c.arc(width / 2, height / 2, width / 2 - 4 * root.u, 0, Math.PI * 2); c.stroke()
                                c.strokeStyle = root.lava
                                c.beginPath(); c.arc(width / 2, height / 2, width / 2 - 4 * root.u, 0, Math.PI * 0.6); c.stroke()
                            }
                            RotationAnimator on rotation {
                                from: 0
                                to: 360
                                duration: 1100
                                loops: Animation.Infinite
                                running: anillo.visible
                            }
                        }
                        Image {
                            anchors.fill: parent
                            visible: root.situacion === 3
                            source: "file:///usr/share/icons/hicolor/128x128/apps/antu-instalador.png"
                            sourceSize.width: 128
                            sourceSize.height: 128
                        }
                        Rectangle {
                            anchors.fill: parent
                            visible: root.situacion === 4
                            radius: width / 2
                            color: "transparent"
                            border.width: 4 * root.u
                            border.color: root.ink3
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: root.titular
                        color: root.ink
                        font.family: "Inter"
                        font.pixelSize: 40 * root.u
                        font.weight: Font.Bold
                    }
                }
                Text {
                    Layout.fillWidth: true
                    visible: text.length > 0
                    wrapMode: Text.WordWrap
                    text: root.detalle
                    color: root.ink2
                    font.family: "Inter"
                    font.pixelSize: 24 * root.u
                    lineHeight: 1.15
                }

                Flow {
                    Layout.fillWidth: true
                    Layout.topMargin: 8 * root.u
                    spacing: 16 * root.u
                    visible: !root.confirmando && root.situacion !== 0
                    LavaButton {
                        u: root.u
                        visible: root.situacion === 3
                        text: "Reiniciar y actualizar"
                        onClicked: backend.reiniciar()
                    }
                    LavaButton {
                        u: root.u
                        primary: root.situacion === 1 || root.situacion === 4
                        visible: root.situacion !== 3
                        enabled: root.situacion !== 2
                        text: "Buscar ahora"
                        onClicked: backend.buscar()
                    }
                    LavaButton {
                        u: root.u
                        primary: false
                        visible: !!root.e.anterior
                        text: "Volver a la versión anterior"
                        onClicked: root.confirmando = true
                    }
                }

                ColumnLayout {
                    visible: root.confirmando
                    spacing: 16 * root.u
                    Text {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: "Antu arrancará con la versión anterior la próxima vez que reinicies. Tus archivos y apps no cambian."
                        color: root.ink
                        font.family: "Inter"
                        font.pixelSize: 24 * root.u
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 16 * root.u
                        LavaButton {
                            u: root.u
                            destructive: true
                            text: "Volver a la anterior"
                            onClicked: { backend.volver(); root.confirmando = false }
                        }
                        LavaButton {
                            u: root.u
                            primary: false
                            text: "Cancelar"
                            onClicked: root.confirmando = false
                        }
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            Layout.topMargin: 32 * root.u
            wrapMode: Text.WordWrap
            text: "Antu baja cada versión nueva en segundo plano, con la prioridad más baja para no molestar mientras juegas, "
                  + "nunca con datos móviles y nunca reinicia solo. Cada versión pasa una prueba completa antes de llegar a tu equipo."
            color: root.ink3
            font.family: "Inter"
            font.pixelSize: 21 * root.u
            lineHeight: 1.15
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
            font.pixelSize: 22 * root.u
        }
        Timer {
            id: avisoReloj
            interval: 6000
            onTriggered: root.avisoTexto = ""
        }
    }
}
