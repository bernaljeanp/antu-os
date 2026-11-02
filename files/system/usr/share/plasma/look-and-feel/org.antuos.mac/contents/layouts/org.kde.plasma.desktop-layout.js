// Antu OS, distribución Mac: barra superior translúcida con menú global, bandeja y hora; dock flotante centrado
// abajo que se aparta cuando una ventana lo tapa.
var bar = new Panel;
bar.location = "top";
bar.height = 2 * Math.ceil(gridUnit * 1.6 / 2);
bar.floating = false;
bar.opacity = "translucent";
var menu = bar.addWidget("org.kde.plasma.kickoff");
menu.currentConfigGroup = ["General"];
menu.writeConfig("icon", "antu");
bar.addWidget("org.kde.plasma.appmenu");
bar.addWidget("org.kde.plasma.panelspacer");
bar.addWidget("org.kde.plasma.systemtray");
var reloj = bar.addWidget("org.kde.plasma.digitalclock");
reloj.currentConfigGroup = ["Appearance"];
reloj.writeConfig("use24hFormat", 2);  // como el inicio de sesión

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
// En el USB en vivo, el lugar del navegador lo toman el instalador y el informe: Brave llega después, desde Flathub.
var live = applicationExists("antu-instalador.desktop") && !applicationExists("com.brave.Browser.desktop");
var primeras = live ? ["applications:antu-instalador.desktop", "applications:antu-informe.desktop"]
                    : ["applications:com.brave.Browser.desktop"];
tasks.writeConfig("launchers", primeras.concat([
    "preferred://filemanager",
    "applications:steam.desktop",
    "applications:org.kde.discover.desktop",
    "applications:zenit.desktop",
    "applications:systemsettings.desktop"
]));

var desktops = desktopsForActivity(currentActivity());
for (var i = 0; i < desktops.length; i++) {
    desktops[i].wallpaperPlugin = "org.kde.image";
}
