"""Catálogo cerrado de preparación. Solo aplicaciones del remoto firmado Flathub."""
APPS = {
    "com.brave.Browser": ("Brave", "Navegador", True),
    "com.heroicgameslauncher.hgl": ("Heroic", "Epic, GOG y Amazon", False),
    "net.lutris.Lutris": ("Lutris", "Otras bibliotecas de juegos", False),
    "com.usebottles.bottles": ("Bottles", "Programas de Windows", False),
    "com.vysp3r.ProtonPlus": ("ProtonPlus", "Versiones adicionales de Proton", False),
    "com.discordapp.Discord": ("Discord", "Voz y comunidad", False),
    "org.vinegarhq.Sober": ("Sober", "Roblox no oficial; compatibilidad variable", False),
    "org.videolan.VLC": ("VLC", "Vídeo y música", False),
    "io.missioncenter.MissionCenter": ("Mission Center", "Uso de recursos", False),
    "com.obsproject.Studio": ("OBS Studio", "Grabación y emisión", False),
    "com.github.wwmm.easyeffects": ("EasyEffects", "Ecualización y efectos de sonido", False),
}


def seleccionar(ids):
    if not isinstance(ids, list) or not ids or len(ids) > len(APPS) or any(not isinstance(i, str) or i not in APPS for i in ids):
        raise ValueError("Selecciona aplicaciones del catálogo de Antu.")
    return list(dict.fromkeys(ids))
