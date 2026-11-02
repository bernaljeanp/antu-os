// Antu OS, distribución Zorin (por defecto): barra inferior flotante y translúcida, con el menú y las apps al
// centro y la bandeja y la hora a la derecha.
var panel = new Panel;
panel.location = "bottom";
panel.height = 2 * Math.ceil(gridUnit * 2.6 / 2);
panel.floating = true;
panel.lengthMode = "fill";
panel.opacity = "translucent";

panel.addWidget("org.kde.plasma.panelspacer");

panel.addWidget("org.kde.plasma.kickoff");

var tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "preferred://filemanager",
    "applications:org.kde.konsole.desktop",
    "applications:systemsettings.desktop"
]);

panel.addWidget("org.kde.plasma.panelspacer");
panel.addWidget("org.kde.plasma.systemtray");
panel.addWidget("org.kde.plasma.digitalclock");

var desktops = desktopsForActivity(currentActivity());
for (var i = 0; i < desktops.length; i++) {
    desktops[i].wallpaperPlugin = "org.kde.image";
}
