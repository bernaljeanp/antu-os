// Antu OS, Inicio: asistente del primer arranque en una sola página. Cada sección se completa y se pliega con su
// resumen; la siguiente se abre. Mismo mundo visual que el inicio de sesión: vidrio de obsidiana y lava.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 2560
    height: 1600
    visible: true
    visibility: Window.FullScreen
    title: "Antu Inicio"
    color: "#0B0B0E"

    readonly property real u: height / 1600
    readonly property color ink: "#F5F5F7"
    readonly property color ink2: "#C7C7CC"
    readonly property color negative: "#FF7069"
    readonly property bool software: GraphicsInfo.api === GraphicsInfo.Software

    property int openSection: 0
    property bool userEdited: false
    property string desktopChoice: "zorin"
    property bool working: false
    property bool failed: false
    property string status: ""

    readonly property bool userValid: /^[a-z][a-z0-9_-]{0,30}$/.test(userField.text)
    readonly property bool accountValid: realName.text.trim().length > 0 && userValid
                                         && password.text.length > 0 && password.text === confirm.text

    function start() {
        if (!accountValid) {
            openSection = 2
            return
        }
        working = true
        failed = false
        backend.apply(language.currentValue, keyboard.currentValue, zone.currentText, realName.text.trim(),
                      userField.text, password.text, desktopChoice, ai.checked)
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

    // Fondo: el de Antu, desenfocado con GPU; sin GPU, solo oscurecido.
    Image {
        id: wallpaper
        anchors.fill: parent
        source: "file:///usr/share/wallpapers/Antu/contents/images_dark/3840x2160.png"
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        visible: root.software
    }
    Rectangle {
        anchors.fill: parent
        visible: root.software
        color: "#000000"
        opacity: 0.55
    }
    MultiEffect {
        anchors.fill: parent
        source: wallpaper
        visible: !root.software && wallpaper.status === Image.Ready
        blurEnabled: true
        blurMax: 64
        blur: 1.0
        brightness: -0.4
    }

    Flickable {
        id: page
        anchors.fill: parent
        contentHeight: content.implicitHeight + 240 * root.u
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

        ColumnLayout {
            id: content
            width: 1040 * root.u
            anchors.horizontalCenter: parent.horizontalCenter
            y: 120 * root.u
            spacing: 22 * root.u

            RowLayout {
                spacing: 28 * root.u
                Layout.bottomMargin: 26 * root.u
                Image {
                    source: "file:///usr/share/antu/antu-symbol.svg"
                    sourceSize.width: 96 * root.u
                    sourceSize.height: 96 * root.u
                }
                ColumnLayout {
                    spacing: 6 * root.u
                    Text {
                        text: "Te damos la bienvenida a Antu"
                        color: root.ink
                        font.family: "Inter"
                        font.pixelSize: 54 * root.u
                        font.weight: Font.Bold
                        font.variableAxes: ({ "opsz": 32 })
                    }
                    Text {
                        text: "Unos pocos pasos y estarás jugando."
                        color: root.ink2
                        font.family: "Inter"
                        font.pixelSize: 26 * root.u
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

                RowLayout {
                    spacing: 18 * root.u
                    GlassCombo {
                        id: language
                        u: root.u
                        Layout.fillWidth: true
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
                    columns: 2
                    columnSpacing: 18 * root.u
                    rowSpacing: 18 * root.u
                    Layout.fillWidth: true

                    GlassField {
                        id: realName
                        u: root.u
                        Layout.fillWidth: true
                        placeholderText: "Tu nombre"
                        Accessible.name: "Tu nombre"
                        onTextEdited: if (!root.userEdited) userField.text = backend.suggestUser(text)
                    }
                    GlassField {
                        id: userField
                        u: root.u
                        Layout.fillWidth: true
                        placeholderText: "Nombre de usuario"
                        Accessible.name: "Nombre de usuario"
                        invalid: text.length > 0 && !root.userValid
                        onTextEdited: root.userEdited = true
                    }
                    GlassField {
                        id: password
                        u: root.u
                        Layout.fillWidth: true
                        placeholderText: "Contraseña"
                        Accessible.name: "Contraseña"
                        echoMode: TextInput.Password
                        passwordCharacter: "•"
                    }
                    GlassField {
                        id: confirm
                        u: root.u
                        Layout.fillWidth: true
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
                    wrapMode: Text.WordWrap
                    font.family: "Inter"
                    font.pixelSize: 21 * root.u
                    color: userField.invalid || confirm.invalid ? root.negative : root.ink2
                    text: userField.invalid ? "El usuario empieza con una letra y solo usa minúsculas, números, - y _."
                        : confirm.invalid ? "Las contraseñas no coinciden."
                        : password.text.length > 0 && password.text.length < 8
                          ? "Contraseña corta: funciona, pero te recomendamos 8 caracteres o más."
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

                RowLayout {
                    spacing: 22 * root.u
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
                            implicitHeight: 360 * root.u
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
                                    text: choice.modelData.label
                                    color: root.ink
                                    font.family: "Inter"
                                    font.pixelSize: 24 * root.u
                                    font.weight: Font.DemiBold
                                }
                                Text {
                                    text: choice.modelData.note
                                    color: root.ink2
                                    font.family: "Inter"
                                    font.pixelSize: 20 * root.u
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
                summary: ai.checked ? "Con IA local" : "Sin extras"
                done: root.openSection > 4
                open: root.openSection === 4
                onHeaderClicked: root.openSection = 4

                Switch {
                    id: ai
                    text: "Instalar IA local (Alpaca con Ollama, unos 4 GB)"
                    font.family: "Inter"
                    font.pixelSize: 23 * root.u
                    palette.windowText: root.ink
                    palette.text: root.ink
                    palette.highlight: "#E2480F"
                    palette.mid: Qt.rgba(1, 1, 1, 0.3)
                    Accessible.name: text
                }
                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    color: root.ink2
                    font.family: "Inter"
                    font.pixelSize: 21 * root.u
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
                    running: root.working
                    implicitWidth: 44 * root.u
                    implicitHeight: 44 * root.u
                    palette.dark: "#FF5A1F"
                }
                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    color: root.failed ? root.negative : root.ink2
                    font.family: "Inter"
                    font.pixelSize: 22 * root.u
                    text: root.status.length > 0 ? root.status
                        : root.accountValid ? "" : "Completa tu cuenta para empezar."
                }
            }
        }
    }
}
