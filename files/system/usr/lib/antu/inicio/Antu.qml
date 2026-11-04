pragma Singleton
import QtQuick

QtObject {
    readonly property SystemPalette sistema: SystemPalette { colorGroup: SystemPalette.Active }
    readonly property bool dark: sistema.window.hslLightness < 0.5
    readonly property color ink: sistema.text
    readonly property color secondary: dark ? "#C7C7CC" : "#4F4F57"
    readonly property color muted: dark ? "#A1A1A6" : "#5E5E64"
    readonly property color base: sistema.base
    readonly property color window: sistema.window
    readonly property color raised: dark ? "#2A2A31" : "#FFFFFF"
    readonly property color raisedHover: dark ? "#35353E" : "#EDEDF0"
    readonly property color edge: dark ? "#55555F" : "#9999A2"
    readonly property color softEdge: dark ? "#3C3C45" : "#D0D0D6"
    readonly property color lava: dark ? "#FF783D" : "#AE330C"
    readonly property color selection: "#B9370D"
    readonly property color negative: dark ? "#FF8B83" : "#B8251A"
    readonly property color positive: dark ? "#57D98B" : "#0B6E39"
    readonly property color warning: dark ? "#F5C451" : "#805500"
    readonly property color fieldTop: dark ? "#141418" : "#F2F2F5"
    readonly property color fieldBottom: dark ? "#24242B" : "#FFFFFF"
    readonly property real motionFactor: typeof antuPreferencias !== "undefined" ? antuPreferencias.factorAnimacion : 1
    readonly property int bodySize: 16
    readonly property int smallSize: 14
    readonly property int radius: 12
    readonly property string symbolSource: "file:///usr/share/antu/" + (dark ? "antu-symbol.svg" : "antu-symbol-light.svg")
    readonly property real textFactor: typeof antuPreferencias !== "undefined" ? antuPreferencias.factorTexto : 1

    function pixels(size, scale) { return Math.round(Math.max(smallSize, size * (scale === undefined ? 1 : scale)) * textFactor) }
    function duration(milliseconds) { return Math.round(milliseconds * motionFactor) }
}
