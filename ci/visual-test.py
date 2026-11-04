#!/usr/bin/env python3
"""Regresiones de arte instalado y preferencias, sin GUI, red ni dispositivos."""
import configparser
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parent.parent


def load(name):
    path = REPO / "files/system/usr/lib/antu/inicio" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prefs = load("preferencias_config")
style = load("estilo")


class Preferences(unittest.TestCase):
    def test_motion_user_preference_overrides_system_and_accepts_zero(self):
        with tempfile.TemporaryDirectory() as folder:
            base, user = Path(folder)/"base", Path(folder)/"user"
            base.write_text("[KDE]\nAnimationDurationFactor=1.5\n")
            user.write_text("[KDE]\nAnimationDurationFactor=0\n")
            self.assertEqual(prefs.factor_animacion([base,user]),0)
            for invalid in ("nan", "inf", "texto"):
                user.write_text("[KDE]\nAnimationDurationFactor="+invalid+"\n")
                self.assertEqual(prefs.factor_animacion([base,user]),1.5)

    def test_motion_bounds_and_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"kdeglobals"
            self.assertEqual(prefs.factor_animacion([path]),1)
            for value,expected in [(-2,0),(0.5,0.5),(9,4)]:
                path.write_text("[KDE]\nAnimationDurationFactor="+str(value)+"\n")
                self.assertEqual(prefs.factor_animacion([path]),expected)

    def test_style_follows_only_antu_and_keeps_customizations(self):
        kde=configparser.ConfigParser();kde.read_string("[KDE]\nwidgetStyle=kvantum\n[General]\nColorScheme=AntuSalar")
        self.assertEqual(style.selection(kde,"AntuObsidiana"),"AntuSalar")
        self.assertIsNone(style.selection(kde,"MiTema"))
        kde["KDE"]["widgetStyle"]="Breeze"
        self.assertIsNone(style.selection(kde,"AntuObsidiana"))

    def test_sync_preserves_other_keys_and_custom_theme_with_spaces(self):
        with tempfile.TemporaryDirectory() as folder:
            config=Path(folder);(config/"Kvantum").mkdir()
            (config/"kdeglobals").write_text("[General]\nColorScheme=AntuSalar\n[KDE]\nwidgetStyle=kvantum\n")
            path=config/"Kvantum/kvantum.kvconfig"
            path.write_text("theme=AntuObsidiana\n[Applications]\nMiTema=app\n")
            style.synchronize(config)
            self.assertEqual(path.read_text(),"theme=AntuSalar\n[Applications]\nMiTema=app\n")
            original="theme = MiTema\n[Applications]\nMiTema=app\n"
            path.write_text(original);style.synchronize(config)
            self.assertEqual(path.read_text(),original)


class Artwork(unittest.TestCase):
    def test_plasma_svg_paintservers_resolve(self):
        for path in (REPO/"files/system/usr/share/plasma/desktoptheme/antu").rglob("*.svg"):
            text=path.read_text(encoding="utf-8")
            ids={node.attrib["id"] for node in ET.fromstring(text).iter() if "id" in node.attrib}
            for reference in re.findall(r"url\(#([^\)]+)\)",text):
                self.assertIn(reference,ids,str(path)+": "+reference)

    def test_every_installed_png_matches_the_measured_artifact(self):
        data=json.loads((REPO/"brand/icon-theme-validation.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["assets"]),464)
        self.assertEqual(data["contrast_failures"],[])
        for record in data["assets"]:
            raw=(REPO/record["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),record["sha256"],record["path"])
            self.assertEqual(struct.unpack(">II",raw[16:24]),(record["size"],)*2)
            self.assertEqual(raw[25],6)  # PNG RGBA
            for bg in ("panel","window"):
                self.assertGreaterEqual(record["contrast"][bg]["outline_p90"],3,record["path"])
                self.assertGreaterEqual(record["contrast"][bg]["visible_p90"],3,record["path"])
            self.assertGreaterEqual(record["contrast"]["light"]["visible_p90"],3)

    def test_both_layouts_use_the_packaged_style_and_icons(self):
        for name in ("org.antuos.desktop","org.antuos.mac"):
            data=(REPO/f"files/system/usr/share/plasma/look-and-feel/{name}/contents/defaults").read_text()
            self.assertIn("widgetStyle=kvantum",data)
            self.assertIn("[kdeglobals][Icons]\nTheme=Antu",data)
        for name in style.THEMES:
            folder=REPO/"files/system/usr/share/Kvantum"/name
            self.assertTrue((folder/(name+".svg")).is_file())
            self.assertTrue((folder/(name+".kvconfig")).is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
