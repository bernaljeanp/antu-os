"""Antu system theme: requested names, original motifs and optical sizes.

Original Antu OS artwork, CC-BY-SA-4.0. No stock icon or vendor logo assets.
This module contains data only; importing it writes nothing.
"""
SIZES = (16, 22, 24, 32, 48, 64, 128, 256)
CONTEXTS = {"places": "Places", "devices": "Devices", "mimetypes": "MimeTypes", "apps": "Applications"}
CATALOG = {
    "places": {
        "folder": "folder",
        "folder-open": "open",
        "user-home": "home",
        "user-desktop": "display",
        "folder-documents": "document",
        "folder-download": "download",
        "folder-music": "music",
        "folder-pictures": "picture",
        "folder-videos": "video",
        "folder-templates": "template",
        "folder-publicshare": "share",
        "folder-games": "gamepad",
        "folder-remote": "remote",
        "network-workgroup": "network",
        "user-trash": "trash",
        "user-trash-full": "trash-full",
        "start-here": "antu-symbol",
    },
    "devices": {
        "drive-harddisk": "harddisk",
        "drive-harddisk-solidstate": "ssd",
        "drive-removable-media-usb": "usb",
        "media-optical": "optical",
        "computer-laptop": "laptop",
        "input-gaming": "gamepad",
        "input-keyboard": "keyboard",
        "input-mouse": "mouse",
        "audio-headphones": "headphones",
        "audio-speakers": "speakers",
        "video-display": "display",
        "phone": "phone",
        "printer": "printer",
    },
    "mimetypes": {
        "text-plain": "text",
        "text-x-generic": "text",
        "image-x-generic": "picture",
        "video-x-generic": "video",
        "audio-x-generic": "music",
        "application-pdf": "sealed-document",
        "application-x-archive": "archive",
        "application-zip": "archive",
        "application-x-executable": "executable",
        "application-x-iso9660-image": "optical",
        "application-vnd.appimage": "package",
        "x-office-document": "document",
        "x-office-spreadsheet": "spreadsheet",
        "x-office-presentation": "presentation",
        "text-x-script": "script",
        "application-x-desktop": "display",
    },
    "apps": {
        "systemsettings": "settings",
        "org.kde.dolphin": "files",
        "org.kde.konsole": "terminal",
        "org.kde.discover": "discover",
        "org.kde.kate": "editor",
        "org.kde.ark": "archive",
        "org.kde.gwenview": "picture",
        "org.kde.spectacle": "capture",
        "org.kde.kcalc": "calculator",
        "preferences-desktop-display": "display",
        "preferences-system-network": "globe",
        "preferences-desktop-sound": "sound",
    },
}
ALIASES = {"text-x-generic": "text-plain", "application-zip": "application-x-archive"}
# Single accent on objects/apps; restrained material-coded accents on document types.
MIME_ACCENTS = {
    "text": "neutral", "picture": "sage", "video": "copper", "music": "steel",
    "sealed-document": "brick", "archive": "copper", "executable": "lava",
    "optical": "neutral", "package": "amber", "document": "steel",
    "spreadsheet": "sage", "presentation": "amber", "script": "steel", "display": "neutral",
}
