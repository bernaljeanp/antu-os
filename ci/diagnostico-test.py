#!/usr/bin/env python3
"""Regresiones del informe físico: sin Qt, sin red, sin privilegios y sin tocar dispositivos reales.

python3 ci/diagnostico-test.py
"""
import importlib.machinery
import importlib.util
import json
import pathlib
import shutil
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

REPO = pathlib.Path(__file__).resolve().parent.parent


def cargar(nombre, ruta):
    loader = importlib.machinery.SourceFileLoader(nombre, str(REPO / ruta))
    spec = importlib.util.spec_from_loader(nombre, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


helper = cargar("informe_helper_test", "files/live/usr/lib/antu/informe-helper")
registro = cargar("registro_test", "files/live/usr/lib/antu/informe/registro.py")
bluetooth = cargar("bluetooth_test", "files/system/usr/lib/antu/bluetooth-mt7925.py")
zenit = cargar("zenit_test", "files/system/usr/lib/antu/zenit/zenit.py")


def escribir(raiz, nombre, valor):
    ruta = raiz / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(valor)
    return ruta


def dato(segundo, temperatura=61, contador=0):
    return {"hora": "2026-11-03T18:32:00+00:00", "segundo": segundo, "cpu_uso": 3,
            "grafica": "dormida", "zenit": {"temperaturas": {"CPU": temperatura}},
            "limites_termicos": {"cpu0/package_throttle_count": contador}}


class Informe(unittest.TestCase):
    def test_captura_agotada_no_ejecuta_mas_comandos(self):
        token = helper.LIMITE.set(time.monotonic() - 1)
        try:
            with patch.object(helper.subprocess, "run") as comando:
                self.assertIn("se agotó", helper.correr(["programa-de-prueba"]))
                comando.assert_not_called()
        finally:
            helper.LIMITE.reset(token)

    @unittest.skipUnless(shutil.which("systemd-tmpfiles"), "requiere systemd-tmpfiles")
    def test_dns_reemplaza_archivo_privado_antes_del_servicio(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            privado = escribir(raiz, "etc/resolv.conf", "")
            privado.chmod(0o700)
            escribir(raiz, "run/systemd/resolve/stub-resolv.conf", "nameserver 127.0.0.53\n").chmod(0o644)
            escribir(raiz, "usr/lib/tmpfiles.d/antu-dns.conf", (REPO / "files/system/usr/lib/tmpfiles.d/antu-dns.conf").read_text())
            subprocess.run(["systemd-tmpfiles", "--root=" + tmp, "--create"], check=True, capture_output=True)
            self.assertTrue(privado.is_symlink())
            self.assertEqual(privado.read_text(), "nameserver 127.0.0.53\n")
            self.assertEqual(privado.stat().st_mode & 0o777, 0o644)

    def test_privacidad_y_versiones(self):
        helper.autoprueba()
        with patch.object(helper.socket, "gethostname", return_value="Nombre-Privado"):
            texto = helper.limpiar("Nombre-Privado kernel: aviso\nHost Name: Nombre-Privado\nUser Name: Persona")
        self.assertNotIn("Nombre-Privado", texto)
        self.assertNotIn("Persona", texto)

    def test_rechaza_otro_disco(self):
        def correr(orden):
            return "/dev/sdb1" if orden[0] == "findmnt" else ("sda" if "PKNAME" in orden and orden[-1] != "/dev/sdb1" else "sdb")
        with patch.object(helper.os.path, "exists", return_value=True), patch.object(helper, "correr", side_effect=correr):
            self.assertIsNone(helper.particion_del_usb())

    def test_nombre_no_admite_rutas(self):
        for nombre in ("../../archivo.txt", "/etc/resolv.conf", "informe-enlace.txt"):
            with self.assertRaises(ValueError):
                helper.en_el_usb(nombre, b"datos")

    def test_guardado_atomico_y_fallo_sin_perder_anterior(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            punto = raiz / "montaje"
            punto.mkdir()
            nombre = "informe-live-20261103-183200.txt"
            anterior = punto / nombre
            anterior.write_bytes(b"informe anterior")
            with (patch.object(helper, "particion_del_usb", return_value="/dev/falso"),
                  patch.object(helper, "CERROJO_USB", str(raiz / "lock")),
                  patch.object(helper.tempfile, "mkdtemp", return_value=str(punto)),
                  patch.object(helper.subprocess, "run") as comando):
                with patch.object(helper.os, "fsync", side_effect=OSError("USB sin espacio")):
                    self.assertFalse(helper.en_el_usb(nombre, b"nuevo"))
                self.assertEqual(anterior.read_bytes(), b"informe anterior")
                self.assertTrue(helper.en_el_usb(nombre, b"nuevo"))
                self.assertEqual(anterior.read_bytes(), b"nuevo")
                self.assertEqual(comando.call_args.args[0][0], "umount")

    def test_no_copia_si_no_es_usb_de_arranque(self):
        with patch.object(helper, "particion_del_usb", return_value=None), patch.object(helper.subprocess, "run") as comando:
            self.assertFalse(helper.en_el_usb("informe-20261103-183200.txt", b"contenido"))
            comando.assert_not_called()


class Registro(unittest.TestCase):
    def test_gpu_dormida_no_se_despierta(self):
        with patch.object(registro, "nvidia_despierta", return_value=False), patch.object(registro, "correr") as comando:
            with patch.object(registro, "zenit", return_value={"temperaturas": {}}):
                muestra, _ = registro.muestra()
        comando.assert_not_called()
        self.assertIn("no se despierta", muestra["grafica"])

    def test_solo_nvidia_grafica_activa(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            for archivo, valor in (("a/vendor", "0x10de"), ("a/class", "0x030000"), ("a/power/runtime_status", "suspended"),
                                   ("b/vendor", "0x10de"), ("b/class", "0x040300"), ("b/power/runtime_status", "active")):
                escribir(raiz, archivo, valor)
            self.assertFalse(registro.nvidia_despierta(raiz))
            escribir(raiz, "a/power/runtime_status", "active")
            self.assertTrue(registro.nvidia_despierta(raiz))

    def test_una_muestra_no_equivale_a_prueba_sostenida(self):
        texto = registro.resumen([dato(100, 96)])
        self.assertIn("máxima 96", texto)
        self.assertIn("no permite saber", texto)
        self.assertIn("0 s", texto)

    def test_intervalo_real_y_contadores(self):
        datos = [dato(100 + i * 5, 61 + i, i) for i in range(13)]
        texto = registro.resumen(datos)
        self.assertIn("60 s", texto)
        self.assertIn("máxima 73", texto)
        self.assertIn("+12", texto)
        self.assertNotIn("Registro breve", texto)

    def test_lectura_tolera_ultima_linea_incompleta(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            escribir(raiz, "mediciones.jsonl", json.dumps(dato(0)) + "\n{" )
            self.assertEqual(len(registro.mediciones(raiz)), 1)

    def test_captura_no_se_pierde_al_reiniciar_servicio(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            escribir(raiz, "mediciones.jsonl", json.dumps(dato(0)) + "\n{")
            escribir(raiz, "estado.json", json.dumps({"archivo": "informe-live-20261103-183200.txt"}))
            exportados = []
            ayudante = {"limpiar": lambda t: t, "en_el_usb": lambda n, c: exportados.append((n, c)) or True}
            def guardar(_helper, nombre, carpeta):
                escribir(carpeta, "avance.txt", "Informe automático\n\n===== Registro mientras se probaba =====\nviejo")
                return True
            with (patch.object(registro.runpy, "run_path", return_value=ayudante),
                  patch.object(registro, "MAX_MUESTRAS", 2), patch.object(registro, "CADA", 0),
                  patch.object(registro, "muestra", return_value=(dato(5), None)),
                  patch.object(registro, "guardar_avance", side_effect=guardar)):
                registro.ejecutar(raiz)
            datos = registro.mediciones(raiz)
            self.assertEqual([d["segundo"] for d in datos], [0, 5])
            estado = json.loads((raiz / "estado.json").read_text())
            self.assertFalse(estado["activo"])
            self.assertTrue(estado["usb"])
            self.assertEqual(estado["muestras"], 2)
            self.assertEqual(exportados[-1][0], "informe-live-20261103-183200.txt")
            self.assertIn(b'"segundo": 5', exportados[-1][1])


class Sensores(unittest.TestCase):
    def test_cpu_del_procesador_gana_al_firmware(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            for archivo, valor in (("hwmon0/name", "alienware_wmi"), ("hwmon0/temp1_label", "CPU"),
                                   ("hwmon0/temp1_input", "61000"), ("hwmon8/name", "coretemp"),
                                   ("hwmon8/temp1_label", "Package id 0"), ("hwmon8/temp1_input", "96000"),
                                   ("hwmon8/temp2_label", "Core 0"), ("hwmon8/temp2_input", "99000")):
                escribir(raiz, "sys/class/hwmon/" + archivo, valor)
            with patch.object(zenit, "RAIZ", tmp):
                self.assertEqual(zenit.sensores()[0]["CPU"], 96)

    def test_sensor_vacio_no_es_cero_ni_derriba_zenit(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            for archivo, valor in (("name", "coretemp"), ("temp1_label", "Package id 0"), ("temp1_input", ""), ("fan1_input", "")):
                escribir(raiz, "sys/class/hwmon/hwmon0/" + archivo, valor)
            with patch.object(zenit, "RAIZ", tmp):
                self.assertEqual(zenit.sensores(), ({}, {}))


class Bluetooth(unittest.TestCase):
    def dispositivo(self, raiz):
        for archivo, valor in (("idVendor", "0489"), ("idProduct", "e139"), ("authorized", "1"),
                               ("usb:1.0/bluetooth/hci0/address", "11:22:33:44:55:66")):
            escribir(raiz, "1-2/" + archivo, valor)
        return raiz / "1-2"

    def test_solo_adaptador_identificado(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            correcto = self.dispositivo(raiz)
            escribir(raiz, "2-1/idVendor", "8087")
            escribir(raiz, "2-1/idProduct", "e139")
            self.assertEqual(bluetooth.dispositivos(raiz), [correcto])

    def test_no_reinicia_bluetooth_que_funciona(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self.dispositivo(pathlib.Path(tmp))
            with patch.object(bluetooth, "correr", return_value="Controller 11:22:33:44:55:66 equipo"):
                self.assertFalse(bluetooth.recuperar(d))
            self.assertEqual((d / "authorized").read_text(), "1")

    def test_no_reinicia_sin_fallo_atribuible(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = self.dispositivo(pathlib.Path(tmp))
            with (patch.object(bluetooth, "reconocido", return_value=False),
                  patch.object(bluetooth, "bloqueado", return_value=False),
                  patch.object(bluetooth, "correr", return_value="Bluetooth: hci9: Failed to send wmt func ctrl (-110)")):
                self.assertFalse(bluetooth.recuperar(d))

    def test_respeta_bluetooth_apagado(self):
        with patch.object(bluetooth, "correr", return_value="bluetooth blocked unblocked"):
            self.assertTrue(bluetooth.bloqueado())
        with patch.object(bluetooth, "correr", return_value="bluetooth unblocked unblocked"):
            self.assertFalse(bluetooth.bloqueado())

    def test_un_intento_y_reautoriza_al_interrumpir(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = pathlib.Path(tmp)
            d = self.dispositivo(raiz)
            with (patch.object(bluetooth, "MARCA", raiz / "marca"),
                  patch.object(bluetooth, "reconocido", return_value=False),
                  patch.object(bluetooth, "bloqueado", return_value=False),
                  patch.object(bluetooth, "fallo_wmt", return_value=True),
                  patch.object(bluetooth.time, "sleep", side_effect=InterruptedError)):
                with self.assertRaises(InterruptedError):
                    bluetooth.recuperar(d)
                self.assertEqual((d / "authorized").read_text(), "1")
                self.assertFalse(bluetooth.recuperar(d))


if __name__ == "__main__":
    unittest.main(verbosity=2)
