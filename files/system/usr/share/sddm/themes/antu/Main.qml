// Antu OS: inicio de sesión al estilo macOS en versión gamer: vidrio de obsidiana y un solo acento de lava.
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts

Rectangle {
    id: root
    width: 2560
    height: 1600
    color: "#0B0B0E"

    // 1 px del diseño de referencia (1600 px de alto); todo escala con la pantalla.
    readonly property real u: height / 1600
    readonly property color ink: "#F5F5F7"
    readonly property color ink2: "#C7C7CC"
    readonly property color glass: Qt.rgba(1, 1, 1, 0.14)
    readonly property color glassHover: Qt.rgba(1, 1, 1, 0.24)
    readonly property color glassEdge: Qt.rgba(1, 1, 1, 0.20)
    readonly property color lava: "#FF5A1F"
    readonly property color lavaDeep: "#C93A0C"
    readonly property color negative: "#FF7069"
    readonly property color menu: "#1C1C21"
    readonly property string face: "Inter"

    property int current: userModel.lastIndex >= 0 ? userModel.lastIndex : 0
    property var currentUser: null
    property bool failed: false
    property date now: new Date()

    onCurrentChanged: currentUser = users.itemAt(current)

    function capitalized(text) {
        return text.charAt(0).toUpperCase() + text.slice(1)
    }

    function login() {
        const name = users.count > 0 && currentUser ? currentUser.uName : usernameField.text
        if (name.length === 0)
            return
        failed = false
        sddm.login(name, password.text, session.currentIndex)
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            password.text = ""
            root.failed = true
            shake.restart()
            password.forceActiveFocus()
        }
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: root.now = new Date()
    }

    // Cuentas que expone SDDM; los delegados guardan los datos que usa la pantalla.
    Item {
        visible: false
        Repeater {
            id: users
            model: userModel
            delegate: Item {
                required property string name
                required property string realName
                readonly property string uName: name
                readonly property string uReal: realName.length > 0 ? realName : name
            }
            onItemAdded: (index, item) => {
                if (index === root.current)
                    root.currentUser = item
            }
        }
    }

    // Fondo: el fondo de pantalla de Antu, desenfocado y oscurecido como en el bloqueo de macOS.
    // Sin GPU (dibujo por software, por ejemplo en una VM sin 3D) no hay desenfoque: se muestra solo oscurecido.
    readonly property bool software: GraphicsInfo.api === GraphicsInfo.Software
    Image {
        id: wallpaper
        anchors.fill: parent
        source: "file:///usr/share/wallpapers/Antu/contents/images_dark/3840x2160.jpg"
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        visible: root.software
    }
    Rectangle {
        anchors.fill: parent
        visible: root.software
        color: "#000000"
        opacity: 0.5
    }
    MultiEffect {
        anchors.fill: parent
        source: wallpaper
        visible: !root.software && wallpaper.status === Image.Ready
        blurEnabled: true
        blurMax: 64
        blur: 1.0
        brightness: -0.35
    }

    // Fecha y hora arriba al centro.
    Column {
        anchors.horizontalCenter: parent.horizontalCenter
        y: 130 * root.u
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.capitalized(Qt.locale("es_CL").toString(root.now, "dddd d 'de' MMMM"))
            color: root.ink2
            font.family: root.face
            font.pixelSize: 34 * root.u
            font.weight: Font.DemiBold
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Qt.formatTime(root.now, "H:mm")
            color: root.ink
            font.family: root.face
            font.pixelSize: 200 * root.u
            font.weight: Font.Bold
            font.features: ({ "tnum": 1 })
            font.variableAxes: ({ "opsz": 32 })
        }
    }

    // Sesión y teclado arriba a la derecha.
    Row {
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 40 * root.u
        spacing: 12 * root.u

        ComboBox {
            id: session
            visible: count > 1  // como en macOS: solo se ofrece cuando hay algo que elegir
            model: sessionModel
            textRole: "name"
            currentIndex: sessionModel.lastIndex
            implicitHeight: 48 * root.u
            font.family: root.face
            font.pixelSize: 20 * root.u
            palette.buttonText: root.ink
            palette.text: root.ink
            palette.window: root.menu
            palette.base: root.menu
            palette.highlight: root.lavaDeep
            palette.highlightedText: "#FFFFFF"
            palette.dark: root.ink2
            Accessible.name: "Sesión"
            background: Rectangle {
                radius: height / 2
                color: session.hovered ? root.glassHover : root.glass
                border.width: session.visualFocus ? 2 * root.u : 1
                border.color: session.visualFocus ? root.lava : root.glassEdge
            }
        }

        ComboBox {
            id: layoutPicker
            visible: keyboard.layouts.length > 1
            model: keyboard.layouts
            textRole: "longName"
            currentIndex: keyboard.currentLayout
            onActivated: keyboard.currentLayout = currentIndex
            implicitHeight: 48 * root.u
            font.family: root.face
            font.pixelSize: 20 * root.u
            palette.buttonText: root.ink
            palette.text: root.ink
            palette.window: root.menu
            palette.base: root.menu
            palette.highlight: root.lavaDeep
            palette.highlightedText: "#FFFFFF"
            palette.dark: root.ink2
            Accessible.name: "Distribución de teclado"
            background: Rectangle {
                radius: height / 2
                color: layoutPicker.hovered ? root.glassHover : root.glass
                border.width: layoutPicker.visualFocus ? 2 * root.u : 1
                border.color: layoutPicker.visualFocus ? root.lava : root.glassEdge
            }
        }
    }

    // Cuenta, contraseña y estado al centro.
    ColumnLayout {
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height * 0.55
        spacing: 20 * root.u

        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            visible: users.count > 0
            implicitWidth: 136 * root.u
            implicitHeight: implicitWidth
            radius: width / 2
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#FF7A45" }
                GradientStop { position: 1.0; color: root.lavaDeep }
            }
            Text {
                anchors.centerIn: parent
                text: root.currentUser ? root.currentUser.uReal.charAt(0).toUpperCase() : ""
                color: "#FFFFFF"
                font.family: root.face
                font.pixelSize: 60 * root.u
                font.weight: Font.DemiBold
            }
        }

        Text {
            Layout.alignment: Qt.AlignHCenter
            visible: users.count > 0
            text: root.currentUser ? root.currentUser.uReal : ""
            color: root.ink
            font.family: root.face
            font.pixelSize: 36 * root.u
            font.weight: Font.DemiBold
        }

        TextField {
            id: usernameField
            visible: users.count === 0
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 440 * root.u
            Layout.preferredHeight: 64 * root.u
            placeholderText: "Usuario"
            color: root.ink
            placeholderTextColor: root.ink2
            selectionColor: root.lavaDeep
            selectedTextColor: "#FFFFFF"
            font.family: root.face
            font.pixelSize: 24 * root.u
            leftPadding: 26 * root.u
            verticalAlignment: TextInput.AlignVCenter
            Accessible.name: "Usuario"
            onAccepted: password.forceActiveFocus()
            background: Rectangle {
                radius: height / 2
                color: root.glass
                border.width: usernameField.activeFocus ? 2 * root.u : 1
                border.color: usernameField.activeFocus ? root.lava : root.glassEdge
            }
        }

        // La píldora de contraseña se sacude cuando la contraseña falla, como en macOS.
        TextField {
            id: password
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 440 * root.u
            Layout.preferredHeight: 64 * root.u
            echoMode: TextInput.Password
            passwordCharacter: "•"
            placeholderText: "Contraseña"
            color: root.ink
            placeholderTextColor: root.ink2
            selectionColor: root.lavaDeep
            selectedTextColor: "#FFFFFF"
            font.family: root.face
            font.pixelSize: 24 * root.u
            leftPadding: 26 * root.u
            rightPadding: 72 * root.u
            verticalAlignment: TextInput.AlignVCenter
            Accessible.name: "Contraseña"
            transform: Translate { id: shakeOffset }
            onAccepted: root.login()
            onTextEdited: root.failed = false
            Keys.onEscapePressed: text = ""
            background: Rectangle {
                radius: height / 2
                color: root.glass
                border.width: password.activeFocus ? 2 * root.u : 1
                border.color: password.activeFocus ? root.lava : root.glassEdge
            }

            RoundButton {
                id: enter
                anchors.right: parent.right
                anchors.rightMargin: 8 * root.u
                anchors.verticalCenter: parent.verticalCenter
                width: 48 * root.u
                height: width
                focusPolicy: Qt.NoFocus
                Accessible.name: "Entrar"
                onClicked: root.login()
                background: Rectangle {
                    radius: width / 2
                    color: enter.down ? root.lavaDeep : root.lava
                }
                contentItem: Image {
                    source: "arrow.svg"
                    sourceSize.width: 22 * root.u
                    sourceSize.height: 22 * root.u
                    fillMode: Image.PreserveAspectFit
                    horizontalAlignment: Image.AlignHCenter
                    verticalAlignment: Image.AlignVCenter
                }
            }
        }

        Text {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredHeight: 30 * root.u
            text: root.failed ? "Contraseña incorrecta. Inténtalo de nuevo."
                              : (keyboard.capsLock ? "Bloq Mayús activado" : "")
            color: root.failed ? root.negative : root.ink2
            font.family: root.face
            font.pixelSize: 22 * root.u
        }

        // Con varias cuentas, una fila de avatares para cambiar de usuario.
        Row {
            Layout.alignment: Qt.AlignHCenter
            visible: users.count > 1
            spacing: 18 * root.u
            Repeater {
                model: userModel
                delegate: AbstractButton {
                    id: chip
                    required property int index
                    required property string name
                    required property string realName
                    readonly property string label: realName.length > 0 ? realName : name
                    width: 64 * root.u
                    height: width
                    focusPolicy: Qt.StrongFocus
                    Accessible.name: label
                    onClicked: {
                        root.current = index
                        password.forceActiveFocus()
                    }
                    background: Rectangle {
                        radius: width / 2
                        color: chip.hovered ? root.glassHover : root.glass
                        border.width: chip.index === root.current || chip.visualFocus ? 3 * root.u : 0
                        border.color: root.lava
                    }
                    contentItem: Text {
                        text: chip.label.charAt(0).toUpperCase()
                        color: root.ink
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.family: root.face
                        font.pixelSize: 26 * root.u
                        font.weight: Font.DemiBold
                    }
                }
            }
        }
    }

    // Suspender, reiniciar y apagar abajo al centro.
    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 80 * root.u
        spacing: 64 * root.u

        Repeater {
            model: [
                { label: "Suspender", glyph: "suspend.svg", action: "suspend", available: sddm.canSuspend },
                { label: "Reiniciar", glyph: "restart.svg", action: "reboot", available: sddm.canReboot },
                { label: "Apagar", glyph: "power.svg", action: "powerOff", available: sddm.canPowerOff }
            ]
            delegate: AbstractButton {
                id: powerButton
                required property var modelData
                visible: modelData.available
                width: 120 * root.u
                height: 132 * root.u
                focusPolicy: Qt.StrongFocus
                Accessible.name: modelData.label
                onClicked: sddm[modelData.action]()
                background: null
                contentItem: Column {
                    spacing: 12 * root.u
                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: 76 * root.u
                        height: width
                        radius: width / 2
                        color: powerButton.hovered || powerButton.visualFocus ? root.glassHover : root.glass
                        border.width: powerButton.visualFocus ? 2 * root.u : 1
                        border.color: powerButton.visualFocus ? root.lava : root.glassEdge
                        Image {
                            anchors.centerIn: parent
                            source: powerButton.modelData.glyph
                            sourceSize.width: 34 * root.u
                            sourceSize.height: 34 * root.u
                        }
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: powerButton.modelData.label
                        color: root.ink
                        font.family: root.face
                        font.pixelSize: 21 * root.u
                        font.weight: Font.Medium
                    }
                }
            }
        }
    }

    SequentialAnimation {
        id: shake
        NumberAnimation { target: shakeOffset; property: "x"; to: -18 * root.u; duration: 50; easing.type: Easing.OutQuad }
        NumberAnimation { target: shakeOffset; property: "x"; to: 16 * root.u; duration: 70 }
        NumberAnimation { target: shakeOffset; property: "x"; to: -10 * root.u; duration: 60 }
        NumberAnimation { target: shakeOffset; property: "x"; to: 6 * root.u; duration: 50 }
        NumberAnimation { target: shakeOffset; property: "x"; to: 0; duration: 60; easing.type: Easing.OutExpo }
    }

    Component.onCompleted: (users.count > 0 ? password : usernameField).forceActiveFocus()
}
