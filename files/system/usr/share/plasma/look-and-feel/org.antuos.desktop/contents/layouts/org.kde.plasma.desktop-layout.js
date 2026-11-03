// Antu OS, distribución Zorin (por defecto): barra inferior flotante y translúcida, con el menú y las apps al
// centro y la bandeja y la hora a la derecha.
var panel = new Panel;
panel.location = "bottom";
panel.height = 2 * Math.ceil(gridUnit * 2.6 / 2);
panel.floating = true;
panel.lengthMode = "fill";
panel.opacity = "translucent";

panel.addWidget("org.kde.plasma.panelspacer");

var menu = panel.addWidget("org.kde.plasma.kickoff");
menu.currentConfigGroup = ["General"];
menu.writeConfig("icon", "antu");

var tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
// En el USB en vivo, el lugar del navegador lo toman el instalador y el informe: Brave llega después, desde Flathub.
var live = applicationExists("antu-instalador.desktop") && !applicationExists("com.brave.Browser.desktop");
var primeras = live ? ["applications:antu-instalador.desktop", "applications:antu-informe.desktop"]
                    : ["applications:com.brave.Browser.desktop"];
tasks.writeConfig("launchers", primeras.concat([
    "preferred://filemanager",
    "applications:steam.desktop",
    "applications:antu-biblioteca.desktop",
    "applications:antu-observatorio.desktop",
    "applications:org.kde.discover.desktop",
    "applications:zenit.desktop",
    "applications:systemsettings.desktop"
]));

panel.addWidget("org.kde.plasma.panelspacer");
panel.addWidget("org.kde.plasma.systemtray");
var reloj = panel.addWidget("org.kde.plasma.digitalclock");
reloj.currentConfigGroup = ["Appearance"];
reloj.writeConfig("use24hFormat", 2);  // como el inicio de sesión
// Una sola línea, como en macOS: sin los dos renglones apretados ni la fecha en números.
reloj.writeConfig("dateDisplayFormat", 1);
reloj.writeConfig("dateFormat", "custom");
reloj.writeConfig("customDateFormat", "ddd d MMM");
reloj.writeConfig("autoFontAndSize", false);
reloj.writeConfig("fontFamily", "Inter");
reloj.writeConfig("fontWeight", 500);
reloj.writeConfig("fontSize", 11);

var desktops = desktopsForActivity(currentActivity());
for (var i = 0; i < desktops.length; i++) {
    desktops[i].wallpaperPlugin = "org.kde.image";
}
