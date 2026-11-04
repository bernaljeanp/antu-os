// Una sola vez al actualizar Antu: retirar el acceso fijo de Zenit.
// La ventana abierta sigue siendo una tarea normal; cerrar la ventana deja el control en la bandeja.
// No se reconstruyen paneles ni se cambian los demás accesos de una sesión existente.
var kde = ConfigFile("kdeglobals", "KDE");
var look = kde.readEntry("LookAndFeelPackage");
if (look === "org.antuos.desktop" || look === "org.antuos.mac") {
    var bars = panels();
    for (var p = 0; p < bars.length; ++p) {
        var managers = bars[p].widgets("org.kde.plasma.icontasks");
        for (var t = 0; t < managers.length; ++t) {
            var manager = managers[t];
            manager.currentConfigGroup = ["General"];
            var old = manager.readConfig("launchers", []);
            var launchers = typeof old === "string" ? old.split(",") : Array.prototype.slice.call(old);
            var filtered = launchers.filter(function(launcher) {
                return launcher !== "applications:zenit.desktop"
                    && launcher !== "file:///usr/share/applications/zenit.desktop"
                    && launcher !== "/usr/share/applications/zenit.desktop";
            });
            if (filtered.length !== launchers.length) manager.writeConfig("launchers", filtered);
        }
    }
}
