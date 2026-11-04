// Antu OS, Inicio: asistente del primer arranque en una sola página. Cada sección se completa y se pliega con su
// resumen; la siguiente se abre. Mismo mundo visual que el inicio de sesión: vidrio de obsidiana y lava.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 2560
    height: 1600
    visible: true
    visibility: Window.FullScreen
    title: "Antu Inicio"
    color: Antu.base

    readonly property real u: Math.max(0.72, Math.min(1, height / 1600))
    readonly property color ink: Antu.ink
    readonly property color ink2: Antu.secondary
    readonly property color negative: Antu.negative

    readonly property bool compacta: width < 1120 || Antu.textFactor > 1.4
    property int openSection: 0
    property bool userEdited: false
    property string desktopChoice: "zorin"
    property bool working: false
    property bool failed: false
    property string status: ""

    readonly property bool userValid: /^[a-z][a-z0-9_-]{0,30}$/.test(userField.text)
    readonly property bool accountValid: realName.text.trim().length > 0 && userValid
                                         && password.text.length >= 8 && password.text === confirm.text

    function start() {
        if (!accountValid) {
            openSection = 2
            return
        }
        working = true
        failed = false
        backend.apply(language.currentValue, keyboard.currentValue, zone.currentText, realName.text.trim(),
                      userField.text, password.text, desktopChoice, ai.checked, dev.checked, oficina.checked)
    }

    Connections {
        target: backend
        function onProgress(label) { root.status = label + "…" }
        function onFailed(message) {
            root.working = false
            root.failed = true
            root.status = message
        }
        function onFinished() { root.status = "Listo. Abriendo el inicio de sesión…" }
    }

    // Fondo: el de Antu oscurecido, nítido como en el inicio de sesión. Desenfocado se volvía negro con manchas rojas.
    AntuBackdrop { anchors.fill: parent; photographic: true }

    FocusScroll {
        id: page
        anchors.fill: parent
        contentHeight: content.implicitHeight + 240 * root.u
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        ColumnLayout {
            id: content
            width: Math.min(1040 * root.u * Antu.textFactor, page.width - 64)
            anchors.horizontalCenter: parent.horizontalCenter
            y: 120 * root.u
            spacing: 22 * root.u

            RowLayout {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                spacing: 28 * root.u
                Layout.bottomMargin: 26 * root.u
                Image {
                    source: Antu.symbolSource
                    sourceSize.width: 96 * root.u
                    sourceSize.height: 96 * root.u
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    spacing: 6 * root.u
                    Text {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        wrapMode: Text.WordWrap
                        text: "Te damos la bienvenida a Antu"
                        color: root.ink
                        font.family: "Inter"
                        font.pixelSize: Antu.pixels(54, root.u)
                        font.weight: Font.Bold
                        font.variableAxes: ({ "opsz": 32 })
                    }
                    Text {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        wrapMode: Text.WordWrap
                        text: "Unos pocos pasos y estarás jugando."
                        color: root.ink2
                        font.family: "Inter"
                        font.pixelSize: Antu.pixels(26, root.u)
                    }
                }
            }

            Section {
                u: root.u
                title: "Idioma y teclado"
                summary: language.currentText + " · " + keyboard.currentText
                done: root.openSection > 0
                open: root.openSection === 0
                onHeaderClicked: root.openSection = 0

                GridLayout {
                    columns: root.compacta ? 1 : 2
                    columnSpacing: 18 * root.u
                    rowSpacing: 18 * root.u
                    GlassCombo {
                        id: language
                        u: root.u
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        textRole: "text"
                        valueRole: "value"
                        Accessible.name: "Idioma"
                        model: [
                            { text: "Español (Chile)", value: "es_CL.UTF-8" },
                            { text: "Español (España)", value: "es_ES.UTF-8" },
                            { text: "English (United States)", value: "en_US.UTF-8" }
                        ]
                    }
                    GlassCombo {
                        id: keyboard
                        u: root.u
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        textRole: "text"
                        valueRole: "value"
                        Accessible.name: "Distribución de teclado"
                        model: [
                            { text: "Teclado latinoamericano", value: "latam" },
                            { text: "Teclado español (España)", value: "es" },
                            { text: "Teclado inglés (EE. UU.)", value: "us" }
                        ]
                    }
                }
                LavaButton {
                    u: root.u
                    text: "Continuar"
                    onClicked: root.openSection = 1
                }
            }

            Section {
                u: root.u
                title: "Zona horaria"
                summary: zone.currentText.replace(/_/g, " ")
                done: root.openSection > 1
                open: root.openSection === 1
                onHeaderClicked: root.openSection = 1

                GlassCombo {
                    id: zone
                    u: root.u
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    Accessible.name: "Zona horaria"
                    model: backend.zones()
                    Component.onCompleted: currentIndex = Math.max(0, model.indexOf("America/Santiago"))
                }
                LavaButton {
                    u: root.u
                    text: "Continuar"
                    onClicked: root.openSection = 2
                }
            }

            Section {
                u: root.u
                title: "Tu cuenta"
                summary: root.accountValid ? realName.text.trim() + " (" + userField.text + ")" : ""
                done: root.accountValid && root.openSection !== 2
                open: root.openSection === 2
                onHeaderClicked: root.openSection = 2

                GridLayout {
                    columns: root.compacta ? 1 : 2
                    columnSpacing: 18 * root.u
                    rowSpacing: 18 * root.u
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0

                    GlassField {
                        id: realName
                        u: root.u
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        placeholderText: "Tu nombre"
                        Accessible.name: "Tu nombre"
                        onTextEdited: if (!root.userEdited) userField.text = backend.suggestUser(text)
                    }
                    GlassField {
                        id: userField
                        u: root.u
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        placeholderText: "Nombre de usuario"
                        Accessible.name: "Nombre de usuario"
                        invalid: text.length > 0 && !root.userValid
                        onTextEdited: root.userEdited = true
                    }
                    GlassField {
                        id: password
                        u: root.u
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        placeholderText: "Contraseña"
                        Accessible.name: "Contraseña"
                        echoMode: TextInput.Password
                        passwordCharacter: "•"
                    }
                    GlassField {
                        id: confirm
                        u: root.u
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        placeholderText: "Repite la contraseña"
                        Accessible.name: "Repite la contraseña"
                        echoMode: TextInput.Password
                        passwordCharacter: "•"
                        invalid: text.length > 0 && text !== password.text
                        onAccepted: if (root.accountValid) root.openSection = 3
                    }
                }
                Text {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    wrapMode: Text.WordWrap
                    font.family: "Inter"
                    font.pixelSize: Antu.pixels(21, root.u)
                    color: userField.invalid || confirm.invalid || (password.text.length > 0 && password.text.length < 8)
                       ? root.negative : root.ink2
                    text: userField.invalid ? "El usuario empieza con una letra y solo usa minúsculas, números, - y _."
                        : confirm.invalid ? "Las contraseñas no coinciden."
                        : password.text.length > 0 && password.text.length < 8
                          ? "La contraseña necesita al menos 8 caracteres: con ella también administras el equipo."
                          : "Esta cuenta será la administradora del equipo."
                }
                LavaButton {
                    u: root.u
                    text: "Continuar"
                    enabled: root.accountValid
                    onClicked: root.openSection = 3
                }
            }

            Section {
                u: root.u
                title: "Escritorio"
                summary: root.desktopChoice === "zorin" ? "Barra inferior centrada" : "Barra superior y dock"
                done: root.openSection > 3
                open: root.openSection === 3
                onHeaderClicked: root.openSection = 3

                GridLayout {
                    columns: root.compacta ? 1 : 2
                    columnSpacing: 22 * root.u
                    rowSpacing: 22 * root.u
                    Repeater {
                        model: [
                            { id: "zorin", label: "Barra inferior centrada", note: "Como Zorin y Windows 11. Recomendada." },
                            { id: "mac", label: "Barra superior y dock", note: "Como en un Mac." }
                        ]
                        delegate: AbstractButton {
                            id: choice
                            required property var modelData
                            readonly property bool selected: root.desktopChoice === modelData.id
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            implicitHeight: Math.max(360 * root.u, contentItem.implicitHeight + 24 * root.u)
                            Accessible.name: modelData.label
                            onClicked: root.desktopChoice = modelData.id
                            background: Rectangle {
                                radius: 18 * root.u
                                color: choice.hovered ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(1, 1, 1, 0.07)
                                border.width: choice.selected || choice.visualFocus ? 3 * root.u : 1
                                border.color: choice.selected || choice.visualFocus ? "#FF5A1F" : Qt.rgba(1, 1, 1, 0.16)
                            }
                            contentItem: ColumnLayout {
                                spacing: 14 * root.u
                                // Miniatura del escritorio
                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.minimumWidth: 0
                                    Layout.preferredHeight: 230 * root.u
                                    radius: 12 * root.u
                                    clip: true
                                    gradient: Gradient {
                                        GradientStop { position: 0.0; color: "#16131B" }
                                        GradientStop { position: 1.0; color: "#241A1A" }
                                    }
                                    Rectangle { // barra superior (Mac)
                                        visible: choice.modelData.id === "mac"
                                        width: parent.width
                                        height: 16 * root.u
                                        color: Qt.rgba(1, 1, 1, 0.16)
                                    }
                                    Rectangle { // barra inferior flotante (Zorin) o dock (Mac)
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        anchors.bottom: parent.bottom
                                        anchors.bottomMargin: 12 * root.u
                                        width: parent.width * (choice.modelData.id === "zorin" ? 0.9 : 0.46)
                                        height: 30 * root.u
                                        radius: 10 * root.u
                                        color: Qt.rgba(1, 1, 1, 0.18)
                                        Row {
                                            anchors.centerIn: parent
                                            spacing: 9 * root.u
                                            Repeater {
                                                model: 6
                                                Rectangle {
                                                    required property int index
                                                    width: 16 * root.u
                                                    height: width
                                                    radius: 4 * root.u
                                                    color: index === 0 ? "#FF5A1F" : Qt.rgba(1, 1, 1, 0.55)
                                                }
                                            }
                                        }
                                    }
                                }
                                Text {
                                    Layout.fillWidth: true
                                    Layout.minimumWidth: 0
                                    wrapMode: Text.WordWrap
                                    text: choice.modelData.label
                                    color: root.ink
                                    font.family: "Inter"
                                    font.pixelSize: Antu.pixels(24, root.u)
                                    font.weight: Font.DemiBold
                                }
                                Text {
                                    Layout.fillWidth: true
                                    Layout.minimumWidth: 0
                                    wrapMode: Text.WordWrap
                                    text: choice.modelData.note
                                    color: root.ink2
                                    font.family: "Inter"
                                    font.pixelSize: Antu.pixels(20, root.u)
                                }
                            }
                        }
                    }
                }
                LavaButton {
                    u: root.u
                    text: "Continuar"
                    onClicked: root.openSection = 4
                }
            }

            Section {
                u: root.u
                title: "Extras"
                summary: [oficina.checked ? "Oficina" : "", ai.checked ? "IA local" : "", dev.checked ? "Programar" : ""]
                         .filter(x => x).join(", ") || "Sin extras"
                done: root.openSection > 4
                open: root.openSection === 4
                onHeaderClicked: root.openSection = 4

                Switch {
                    id: oficina
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    contentItem: Text {
                        text: oficina.text
                        font: oficina.font
                        color: root.ink
                        wrapMode: Text.WordWrap
                        leftPadding: oficina.indicator.width + oficina.spacing
                        verticalAlignment: Text.AlignVCenter
                    }
                    checked: true
                    text: "Oficina: WordCraft, DeckCraft, GridCraft y PdfCraft (en desarrollo y aún sin firma digital)"
                    font.family: "Inter"
                    font.pixelSize: Antu.pixels(23, root.u)
                    palette.windowText: root.ink
                    palette.text: root.ink
                    palette.highlight: "#E2480F"
                    palette.mid: Qt.rgba(1, 1, 1, 0.3)
                    Accessible.name: text
                }
                Switch {
                    id: ai
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    contentItem: Text {
                        text: ai.text
                        font: ai.font
                        color: root.ink
                        wrapMode: Text.WordWrap
                        leftPadding: ai.indicator.width + ai.spacing
                        verticalAlignment: Text.AlignVCenter
                    }
                    text: "Instalar IA local (Alpaca con Ollama, unos 4 GB)"
                    font.family: "Inter"
                    font.pixelSize: Antu.pixels(23, root.u)
                    palette.windowText: root.ink
                    palette.text: root.ink
                    palette.highlight: "#E2480F"
                    palette.mid: Qt.rgba(1, 1, 1, 0.3)
                    Accessible.name: text
                }
                Switch {
                    id: dev
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    contentItem: Text {
                        text: dev.text
                        font: dev.font
                        color: root.ink
                        wrapMode: Text.WordWrap
                        leftPadding: dev.indicator.width + dev.spacing
                        verticalAlignment: Text.AlignVCenter
                    }
                    text: "Voy a programar (VS Code, Git, Node, Python, Rust, Go, Claude Code y Codex)"
                    font.family: "Inter"
                    font.pixelSize: Antu.pixels(23, root.u)
                    palette.windowText: root.ink
                    palette.text: root.ink
                    palette.highlight: "#E2480F"
                    palette.mid: Qt.rgba(1, 1, 1, 0.3)
                    Accessible.name: text
                }
                Text {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    wrapMode: Text.WordWrap
                    color: root.ink2
                    font.family: "Inter"
                    font.pixelSize: Antu.pixels(21, root.u)
                    text: "Brave, Steam, tus apps de juegos y la oficina de ArtCraft se instalan solas en cuanto haya internet."
                }
            }

            RowLayout {
                Layout.topMargin: 18 * root.u
                spacing: 24 * root.u
                LavaButton {
                    u: root.u
                    text: root.working ? "Configurando…" : "Empezar a usar Antu"
                    enabled: root.accountValid && !root.working
                    onClicked: root.start()
                }
                BusyIndicator {
                    visible: root.working
                    running: root.working && Antu.motionFactor > 0
                    implicitWidth: 44 * root.u
                    implicitHeight: 44 * root.u
                    palette.dark: "#FF5A1F"
                }
                Text {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    wrapMode: Text.WordWrap
                    color: root.failed ? root.negative : root.ink2
                    font.family: "Inter"
                    font.pixelSize: Antu.pixels(22, root.u)
                    text: root.status.length > 0 ? root.status
                        : root.accountValid ? "" : "Completa tu cuenta para empezar."
                }
            }
        }
    }
}
