// Una superficie de trabajo estable. La fotografía se reserva para la bienvenida.
import QtQuick
import QtQuick.Window

Item {
    id: backdrop
    property bool photographic: false
    property real shade: 0.58
    Rectangle { anchors.fill: parent; color: Antu.base }
    Loader {
        anchors.fill: parent
        active: backdrop.photographic
        sourceComponent: Image {
            source: "file:///usr/share/wallpapers/Paranal/contents/" + (Antu.dark ? "images_dark" : "images") + "/3840x2160.jpg"
            sourceSize.width: Math.min(3840, Math.ceil(width * Screen.devicePixelRatio))
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
        }
    }
    Rectangle { anchors.fill: parent; color: Antu.dark ? "#000000" : "#FFFFFF"; opacity: backdrop.photographic ? backdrop.shade : 0 }
    Rectangle {
        visible: !backdrop.photographic
        width: parent.width
        height: Math.min(150, parent.height / 4)
        gradient: Gradient {
            GradientStop { position: 0; color: Antu.dark ? "#2C2C34" : "#FFFFFF" }
            GradientStop { position: 1; color: Antu.base }
        }
    }
}
