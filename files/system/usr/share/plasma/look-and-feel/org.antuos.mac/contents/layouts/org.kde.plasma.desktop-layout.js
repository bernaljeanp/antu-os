// Antu OS, distribución Mac: barra superior translúcida con menú global, bandeja y hora; dock flotante centrado
// abajo que se aparta cuando una ventana lo tapa.
var bar = new Panel;
bar.location = "top";
bar.height = 2 * Math.ceil(gridUnit * 1.6 / 2);
bar.floating = false;
bar.opacity = "translucent";
var menu = bar.addWidget("org.kde.plasma.kickoff");
menu.currentConfigGroup = ["General"];
menu.writeConfig("icon", "/usr/share/antu/antu-symbol.svg");
bar.addWidget("org.kde.plasma.appmenu");
bar.addWidget("org.kde.plasma.panelspacer");
bar.addWidget("org.kde.plasma.systemtray");
bar.addWidget("org.kde.plasma.digitalclock");

var dock = new Panel;
dock.location = "bottom";
dock.height = 2 * Math.ceil(gridUnit * 3.2 / 2);
dock.floating = true;
dock.lengthMode = "fit";
dock.alignment = "center";
dock.hiding = "dodgewindows";
dock.opacity = "translucent";
var tasks = dock.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "applications:firefox.desktop",
    "preferred://filemanager",
    "applications:steam.desktop",
    "applications:org.kde.discover.desktop",
    "applications:org.kde.konsole.desktop",
    "applications:systemsettings.desktop"
]);

var desktops = desktopsForActivity(currentActivity());
for (var i = 0; i < desktops.length; i++) {
    desktops[i].wallpaperPlugin = "org.kde.image";
}
