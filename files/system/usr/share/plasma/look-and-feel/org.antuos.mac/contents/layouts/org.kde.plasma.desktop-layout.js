// Antu OS, distribución Mac: barra superior translúcida con menú global, bandeja y hora; dock flotante centrado
// abajo que se aparta cuando una ventana lo tapa.
var bar = new Panel;
bar.location = "top";
bar.height = Math.max(32, 2 * Math.ceil(gridUnit * 1.8 / 2));
bar.floating = false;
bar.opacity = "translucent";
var menu = bar.addWidget("org.kde.plasma.kickoff");
menu.currentConfigGroup = ["General"];
menu.writeConfig("icon", "antu");
bar.addWidget("org.kde.plasma.appmenu");
bar.addWidget("org.kde.plasma.panelspacer");
var tray = bar.addWidget("org.kde.plasma.systemtray");
// Plasma anterior usa un contenedor interno; las versiones nuevas configuran la bandeja directamente.
var traySettings = tray;
var trayId = tray.readConfig("SystrayContainmentId", 0);
if (trayId > 0) {
    var embeddedTray = desktopById(trayId);
    if (embeddedTray) traySettings = embeddedTray;
}
traySettings.currentConfigGroup = ["General"];
traySettings.writeConfig("showAllItems", false);
traySettings.writeConfig("scaleIconsToFit", false);
traySettings.writeConfig("iconSpacing", 2);
// Siguen disponibles al desplegar la bandeja; no se desactiva su función.
traySettings.writeConfig("hiddenItems", ["org.kde.plasma.clipboard", "org.kde.plasma.mediacontroller"]);
var clockGap = bar.addWidget("org.kde.plasma.panelspacer");
clockGap.currentConfigGroup = ["General"];
clockGap.writeConfig("expanding", false);
clockGap.writeConfig("length", 12);

var reloj = bar.addWidget("org.kde.plasma.digitalclock");
reloj.currentConfigGroup = ["Appearance"];
reloj.writeConfig("use24hFormat", 2);  // como el inicio de sesión
// Una sola línea, como en macOS: sin los dos renglones apretados ni la fecha en números.
reloj.writeConfig("dateDisplayFormat", 1);
reloj.writeConfig("dateFormat", "custom");
reloj.writeConfig("customDateFormat", "ddd d MMM");
reloj.writeConfig("autoFontAndSize", false);
reloj.writeConfig("fontFamily", "Inter");
reloj.writeConfig("fontWeight", 500);
reloj.writeConfig("fontSize", Math.max(12, Math.round(gridUnit * 2 / 3)));

var dock = new Panel;
dock.location = "bottom";
dock.height = Math.max(56, 2 * Math.ceil(gridUnit * 3 / 2));
dock.floating = true;
dock.lengthMode = "fit";
dock.alignment = "center";
dock.hiding = "dodgewindows";
dock.opacity = "translucent";
var tasks = dock.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
// Accesos esenciales. Zenit vive junto al reloj; Ajustes y Discover se abren desde el menú.
// En el USB, Bienvenida e Informe ocupan el lugar del navegador.
var live = applicationExists("antu-instalador.desktop") && !applicationExists("com.brave.Browser.desktop");
var primeras = live ? ["applications:antu-bienvenida.desktop", "applications:antu-informe.desktop"]
                    : ["applications:com.brave.Browser.desktop"];
tasks.writeConfig("launchers", primeras.concat([
    "preferred://filemanager",
    "applications:steam.desktop",
    "applications:antu-biblioteca.desktop",
    "applications:antu-observatorio.desktop"
]));
// Una sola fila; el grupo ocupa su ancho natural entre los espaciadores.
tasks.writeConfig("fill", false);
tasks.writeConfig("iconSpacing", 2);
tasks.writeConfig("maxStripes", 1);
tasks.writeConfig("groupingStrategy", 1);
tasks.writeConfig("onlyGroupWhenFull", false);
tasks.writeConfig("separateLaunchers", false);
tasks.writeConfig("hideLauncherOnStart", true);

var desktops = desktopsForActivity(currentActivity());
for (var i = 0; i < desktops.length; i++) {
    desktops[i].wallpaperPlugin = "org.kde.image";
}
