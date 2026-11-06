#!/usr/bin/env python3
"""Fallos de firmware y persistencia: nunca toca sysfs real."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

repo = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("zenit", repo / "files/system/usr/lib/antu/zenit/zenit.py")
z = importlib.util.module_from_spec(spec)
spec.loader.exec_module(z)


class Zenit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        z.RAIZ = self.temp.name
        self.profile = "/sys/class/platform-profile/platform-profile-0/"
        for key, value in {"name": "alienware-wmi", "profile": "balanced", "choices": "balanced performance quiet"}.items():
            self.write(self.profile + key, value)
        self.service = z.Zenit(procesos=lambda: [])

    def tearDown(self):
        z.RAIZ = ""
        self.temp.cleanup()

    def write(self, name, value):
        path = Path(z.ruta(name))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)

    def test_no_guarda_un_perfil_que_el_firmware_rechaza(self):
        self.service.guardar()
        before = Path(z.ruta(z.ESTADO)).read_bytes()
        with patch.object(z, "escribir", side_effect=OSError("firmware rechazó")):
            result = self.service.orden(["perfil", "performance"])
        self.assertFalse(result["ok"])
        self.assertEqual(self.service.estado["modo"], "auto")
        self.assertEqual(Path(z.ruta(z.ESTADO)).read_bytes(), before)

    def test_no_confirma_una_escritura_ignorada(self):
        with patch.object(z, "escribir"):
            self.assertFalse(self.service.orden(["perfil", "performance"])["ok"])

    def test_un_perfil_manual_cancela_boost_y_sigilo(self):
        self.service.boost = True
        self.assertTrue(self.service.orden(["perfil", "quiet"])["ok"])
        self.assertFalse(self.service.boost or self.service.sigilo)
        self.assertEqual(z.leer(z.ruta(self.profile + "profile")), "quiet")

    def test_no_ofrece_perfiles_ausentes(self):
        self.assertFalse(self.service.orden(["perfil", "cool"])["ok"])

    def test_guardado_fallido_conserva_el_anterior(self):
        self.service.guardar()
        before = Path(z.ruta(z.ESTADO)).read_bytes()
        with patch.object(z.os, "replace", side_effect=OSError("disco lleno")):
            result = self.service.orden(["perfil", "quiet"])
        self.assertFalse(result["ok"])
        self.assertEqual(Path(z.ruta(z.ESTADO)).read_bytes(), before)
        self.assertEqual(list(Path(z.ruta(z.ESTADO)).parent.glob(".estado-*")), [])

    def test_estado_corrupto_no_impide_arrancar(self):
        for value in ("{", "[]", '{"modo":"turbo","luces":42}', '{"juegos":[]}'):
            self.write(z.ESTADO, value)
            service = z.Zenit(procesos=lambda: [])
            self.assertIn(service.estado["modo"], {"auto", *z.PERFILES})
            self.assertIsInstance(service.estado["luces"], dict)

    def test_limite_no_confirmado_es_error(self):
        self.write("/sys/class/power_supply/BAT0/charge_control_end_threshold", "100")
        with patch.object(z, "escribir"):
            self.assertFalse(self.service.orden(["carga", "80"])["ok"])
        self.assertNotIn("carga", self.service.estado)

    def test_bateria_sin_adaptativa_no_finge_soportarla(self):
        self.write("/sys/class/power_supply/BAT0/charge_control_end_threshold", "80")
        self.assertFalse(self.service.orden(["carga", "adaptativa"])["ok"])
        self.assertFalse(z.capacidades()["carga_adaptativa"])

    def test_error_de_tic_se_expone_sin_caer(self):
        with patch.object(self.service, "aplicar", side_effect=OSError("ocupado")):
            self.service.tic()
        self.assertIn("ocupado", self.service.orden(["estado"])["ultimo_error"])

    def test_salud_de_bateria_y_limite_sin_inventar(self):
        for key, value in {"energy_full": "75000", "energy_full_design": "100000", "capacity": "80"}.items():
            self.write("/sys/class/power_supply/BAT0/" + key, value)
        b = z.bateria()[0]
        self.assertEqual(b["salud_porcentaje"], 75)
        self.assertIsNone(b["ciclos"])
        self.assertEqual(z.limites_termicos(), {})

    def test_no_consulta_nvidia_en_reposo_o_sin_juego(self):
        path = "/sys/bus/pci/devices/0000:01:00.0/"
        for name, value in {"vendor": "0x10de", "class": "0x030000", "power/runtime_status": "suspended"}.items():
            self.write(path + name, value)
        with patch.object(z.subprocess, "run") as run:
            self.assertEqual(z.datos_nvidia(True)["dispositivos"], [])
            self.write(path + "power/runtime_status", "active")
            self.assertEqual(z.datos_nvidia(False)["dispositivos"], [])
            run.assert_not_called()

    def test_nvidia_no_inventa_datos_ausentes(self):
        path = "/sys/bus/pci/devices/0000:01:00.0/"
        for name, value in {"vendor": "0x10de", "class": "0x030000", "power/runtime_status": "active"}.items():
            self.write(path + name, value)
        result = type("Result", (), {"stdout": "65, 99, N/A, 4000, 2100\n"})()
        with patch.object(z.subprocess, "run", return_value=result):
            device = z.datos_nvidia(True)["dispositivos"][0]
        self.assertEqual(device["temperatura"], 65)
        self.assertIsNone(device["vatios"])

    def test_solo_luces_no_escribe_perfiles_bateria_ni_gamemode(self):
        service = z.Zenit(procesos=lambda: ["cs2"], gestion="sistema")
        service.estado["carga"] = "80"
        service.vistos = {123: "cs2"}
        with patch.object(z, "escribir") as write, patch.object(z, "poner_carga") as charge, \
             patch.object(z, "pedir_gamemode") as gamemode, patch.object(z, "poner_luces"):
            service.tic()
            service.restaurar_carga()
            for command in (["perfil", "auto"], ["perfil", "quiet"], ["boost"], ["sigilo"],
                            ["carga", "80"], ["juego", "cs2", "performance"]):
                self.assertFalse(service.orden(command)["ok"], command)
            with patch.object(z, "aviso"):
                service.tecla(z.KEY_F17)
                service.tecla(z.KEY_F20)
            write.assert_not_called()
            charge.assert_not_called()
            gamemode.assert_not_called()
        with patch.object(z, "poner_luces") as lights:
            self.assertTrue(service.orden(["color", "123456", "40"])["ok"])
            lights.assert_called_once_with("123456", 40)
        self.assertEqual(service.orden(["estado"])["gestion"], "sistema")

    def test_cambio_de_gestion_persiste_sin_revertir_el_hardware(self):
        self.assertTrue(self.service.orden(["perfil", "quiet"])["ok"])
        with patch.object(z, "escribir") as write:
            self.assertTrue(self.service.orden(["gestion", "sistema"])["ok"])
            write.assert_not_called()
        restored = z.Zenit(procesos=lambda: [], gestion="zenit")
        self.assertEqual(restored.estado["gestion"], "sistema")
        self.assertTrue(restored.orden(["gestion", "zenit"])["ok"])
        self.assertTrue(restored.orden(["perfil", "performance"])["ok"])
        self.assertEqual(z.leer(z.ruta(self.profile + "profile")), "performance")

    def keyboard(self, event, *codes):
        bits = sum(1 << code for code in codes)
        mask = (1 << (z.struct.calcsize("L") * 8)) - 1
        words = []
        while bits:
            words.append(format(bits & mask, "x"))
            bits >>= z.struct.calcsize("L") * 8
        self.write("/sys/class/input/" + event + "/device/capabilities/key", " ".join(reversed(words)))

    def test_teclado_solo_f18_se_abre_sin_exigir_f17(self):
        self.keyboard("event1", z.KEY_F18)
        self.keyboard("event2", 64, 65, 67)
        with patch.object(z.os, "open", return_value=42) as opened:
            handles = z.teclados()
        self.assertEqual(handles, {"/dev/input/event1": 42})
        opened.assert_called_once()
        self.assertIn(67, z.dispositivos_teclas()["/dev/input/event2"])

    def test_reintenta_teclado_y_cierra_dispositivo_desaparecido(self):
        self.keyboard("event1", z.KEY_F18)
        with patch.object(z.os, "open", side_effect=PermissionError):
            self.assertEqual(z.teclados(), {})
        with patch.object(z.os, "open", return_value=42):
            handles = z.teclados()
        with patch.object(z.os, "open") as opened:
            self.assertEqual(z.teclados(handles), handles)
            opened.assert_not_called()
        self.write("/sys/class/input/event1/device/capabilities/key", "")
        with patch.object(z.os, "close") as closed:
            self.assertEqual(z.teclados(handles), {})
            closed.assert_called_once_with(42)

    def test_prueba_teclas_es_temporal_sin_texto_ni_acciones(self):
        with patch.object(z.time, "monotonic", return_value=100):
            self.assertTrue(self.service.orden(["probar-teclas"])["ok"])
        with patch.object(z.time, "monotonic", return_value=101), patch.object(z, "poner_luces") as lights:
            self.service.tecla(64, "/dev/input/event3")
            self.service.tecla(64, "/dev/input/event3")
            self.service.tecla(z.KEY_F18, "/dev/input/event3")
            self.service.tecla(30, "/dev/input/event3")
            lights.assert_not_called()
            result = self.service.orden(["diagnostico"])["informe"]["teclas"]["prueba"]
        self.assertEqual(result["segundos_restantes"], 14)
        self.assertEqual([v["codigo"] for v in result["eventos"]], [64, z.KEY_F18])
        self.assertEqual(result["eventos"][0]["pulsaciones"], 2)
        with patch.object(z.time, "monotonic", return_value=116):
            self.service.tecla(67, "/dev/input/event3")
            self.assertEqual(len(self.service.estado_prueba_teclas()["eventos"]), 2)
            self.assertEqual(self.service.estado_prueba_teclas()["segundos_restantes"], 0)

    def test_prueba_abre_dispositivos_solo_prog_sin_hacerlo_normalmente(self):
        self.keyboard("event2", 148)
        with patch.object(z.os, "open", return_value=42):
            self.assertEqual(z.teclados(), {})
            self.assertEqual(z.teclados(prueba=True), {"/dev/input/event2": 42})

    def test_f7_en_solo_luces_no_actua_ni_muestra_avisos(self):
        self.service.estado["gestion"] = "sistema"
        previous = {"codigo": z.KEY_F18, "accion": "luces", "aceptada": True}
        self.service.ultima_tecla = previous.copy()
        with patch.object(self.service, "orden") as order, patch.object(z, "aviso") as notice, patch.object(z, "poner_luces") as lights:
            self.service.tecla(z.KEY_F20)
            order.assert_not_called()
            notice.assert_not_called()
            lights.assert_not_called()
        self.assertEqual(self.service.ultima_tecla, previous)
        self.assertFalse(self.service.sigilo)
        self.assertEqual(self.service.diagnostico()["teclas"]["politica_f7"], "escritorio_sin_accion_de_zenit")

    def test_f7_se_conserva_en_gestion_completa(self):
        with patch.object(z, "poner_luces") as lights, patch.object(z, "aviso") as notice:
            self.service.tecla(z.KEY_F20)
            self.assertTrue(self.service.sigilo)
            self.assertTrue(self.service.ultima_tecla["aceptada"])
            lights.assert_called_once_with("FFFFFF", 15)
            notice.assert_called_once()
        self.assertEqual(z.leer(z.ruta(self.profile + "profile")), "quiet")

    def test_prueba_temporal_observa_f7_aunque_se_deje_al_escritorio(self):
        self.service.estado["gestion"] = "sistema"
        with patch.object(z.time, "monotonic", return_value=100):
            self.service.orden(["probar-teclas"])
        with patch.object(z.time, "monotonic", return_value=101), patch.object(z, "aviso") as notice:
            self.service.tecla(z.KEY_F20, "/dev/input/event3")
            notice.assert_not_called()
            self.assertEqual(self.service.estado_prueba_teclas()["eventos"][0]["tecla"], "F20")

    def test_tecla_luces_y_aviso_de_perfil_bloqueado(self):
        self.service.estado["gestion"] = "sistema"
        with patch.object(z, "poner_luces"), patch.object(z, "aviso") as notice:
            self.service.tecla(z.KEY_F18)
            self.assertTrue(self.service.ultima_tecla["aceptada"])
            self.service.tecla(z.KEY_F17)
            self.assertFalse(self.service.ultima_tecla["aceptada"])
            self.assertIn("Solo luces", notice.call_args.args[1])
            last = self.service.ultima_tecla.copy()
            self.service.tecla(30)  # texto normal: no se guarda ni ejecuta ninguna orden
            self.assertEqual(self.service.ultima_tecla, last)
        report = self.service.orden(["diagnostico"])["informe"]
        self.assertTrue(report["teclas"]["f6_f7_bloqueadas_por_modo"])
        self.assertEqual(report["teclas"]["ultima_especial"]["codigo"], z.KEY_F17)

    def test_diagnostico_sin_identificadores_personales_ni_efectos(self):
        self.write("/sys/class/dmi/id/product_name", "Alienware AC16251")
        self.write("/sys/class/dmi/id/sys_vendor", "Dell Inc.")
        self.write("/proc/sys/kernel/osrelease", "6.17-test")
        self.write("/etc/os-release", 'ID=bazzite\nVERSION_ID="43"\nPRETTY_NAME="no_exportar"')
        self.write("/sys/class/dmi/id/product_serial", "SERIAL_PRIVADA")
        self.write("/sys/class/dmi/id/product_uuid", "UUID_PRIVADO")
        self.write("/etc/hostname", "HOST_PRIVADO")
        self.service.estado["juegos"] = {"JUEGO_PRIVADO": "performance"}
        self.service.juego = "JUEGO_PRIVADO"
        self.service.ultimo_error = "/home/USUARIO_PRIVADO/error"
        self.service.error_luces = "ERROR_PRIVADO"
        with patch.object(z, "escribir") as write, patch.object(z, "poner_luces") as lights, \
             patch.object(z, "poner_carga") as charge, patch.object(z.subprocess, "run") as subprocess:
            result = self.service.orden(["diagnostico"])
            write.assert_not_called()
            lights.assert_not_called()
            charge.assert_not_called()
            subprocess.assert_not_called()
        self.assertTrue(result["ok"])
        report = result["informe"]
        self.assertEqual(report["modelo"], "Alienware AC16251")
        self.assertEqual(report["kernel"], "6.17-test")
        self.assertEqual(report["sistema"], {"ID": "bazzite", "VERSION_ID": "43"})
        serialized = json.dumps(report)
        for private in ("SERIAL_PRIVADA", "UUID_PRIVADO", "HOST_PRIVADO", "JUEGO_PRIVADO", "USUARIO_PRIVADO", "ERROR_PRIVADO", "no_exportar"):
            self.assertNotIn(private, serialized)

    def test_diagnostico_distingue_ventiladores_cero_error_y_ausentes(self):
        path = "/sys/class/hwmon/hwmon0/"
        self.write(path + "name", "alienware_wmi")
        self.write(path + "fan1_input", "0")
        self.write(path + "fan2_input", "1200")
        self.write(path + "fan2_fault", "1")
        self.write(path + "fan3_input", "no legible")
        self.write(path + "fan4_input", "2400")
        report = self.service.orden(["diagnostico"])["informe"]
        fans = report["hwmon"][0]["ventiladores"]
        self.assertEqual([f["rpm"] for f in fans], [0, None, None, 2400])
        self.assertEqual(fans[0]["lectura"], "cero_sin_confirmar_parada")
        self.assertEqual(fans[1]["lectura"], "no_disponible")
        self.assertIsNone(report["modelo"])
        self.assertEqual(report["graficas"], [])

    def test_luces_reporte_incompleto_no_se_guarda(self):
        before = dict(self.service.estado["luces"])
        with patch.object(z, "controlador_luces", return_value="/dev/fake"), \
             patch.object(z.os, "open", return_value=9), patch.object(z.os, "close"), \
             patch.object(z.os, "write", return_value=12), patch.object(z.fcntl, "ioctl"):
            self.assertFalse(self.service.orden(["color", "AABBCC", "80"])["ok"])
        self.assertEqual(self.service.estado["luces"], before)
        self.assertIsNone(self.service.luces_envio)
        self.assertIn("incompleto", self.service.error_luces)

    def test_luces_ocupadas_no_envian_reportes(self):
        def busy(fd, cmd, buf):
            buf[2] = 34
        with patch.object(z, "controlador_luces", return_value="/dev/fake"), \
             patch.object(z.os, "open", return_value=9), patch.object(z.os, "close"), \
             patch.object(z.os, "write") as write, patch.object(z.fcntl, "ioctl", side_effect=busy), \
             patch.object(z.time, "sleep"):
            self.assertFalse(self.service.orden(["color", "AABBCC"])["ok"])
            write.assert_not_called()
        self.assertIn("ocupado", self.service.error_luces)

    def test_luces_sin_lectura_no_afirma_color_confirmado(self):
        with patch.object(z, "controlador_luces", return_value="/dev/fake"), \
             patch.object(z.os, "open", return_value=9), patch.object(z.os, "close"), \
             patch.object(z.os, "write", return_value=34), \
             patch.object(z.fcntl, "ioctl", side_effect=OSError("no disponible")):
            result = z.poner_luces("AABBCC", 50)
        self.assertTrue(result["enviado"])
        self.assertFalse(result["controlador_disponible"])
        self.assertFalse(result["color_verificado"])

    def test_luces_registra_ultimo_envio_y_error_posterior(self):
        sent = {"enviado": True, "color": "AABBCC", "brillo": 50, "color_verificado": False}
        with patch.object(z, "poner_luces", return_value=sent):
            self.assertTrue(self.service.orden(["color", "AABBCC", "50"])["ok"])
        with patch.object(z, "poner_luces", side_effect=OSError("USB desconectado")):
            self.assertFalse(self.service.orden(["color", "123456", "40"])["ok"])
        state = self.service.orden(["estado"])
        self.assertEqual(state["luces_envio"], sent)
        self.assertEqual(state["error_luces"], "USB desconectado")
        self.assertEqual(state["luces"]["color"], "AABBCC")

    def test_actualizacion_bazzite_con_estado_antiguo_usa_solo_luces(self):
        self.write(z.ESTADO, '{"modo":"performance","carga":"80","luces":{"color":"123456","brillo":40}}')
        service = z.Zenit(procesos=lambda: [], gestion="sistema")
        self.assertEqual(service.estado["gestion"], "sistema")
        self.assertEqual(service.estado["luces"], {"color": "123456", "brillo": 40})
        with patch.object(z, "escribir") as write, patch.object(z, "poner_carga") as charge:
            service.aplicar()
            service.restaurar_carga()
            write.assert_not_called()
            charge.assert_not_called()

    def test_fallo_al_guardar_gestion_no_confirma_el_cambio(self):
        with patch.object(z.os, "replace", side_effect=OSError("disco lleno")):
            self.assertFalse(self.service.orden(["gestion", "sistema"])["ok"])
        self.assertEqual(self.service.estado["gestion"], "zenit")

    def test_ventiladores_cero_fallo_y_nombres_sin_colisiones(self):
        for chip in ("hwmon0", "hwmon1"):
            path = "/sys/class/hwmon/" + chip + "/"
            self.write(path + "name", "alienware_wmi")
            self.write(path + "fan1_label", "CPU")
            self.write(path + "fan1_input", "0" if chip == "hwmon0" else "2500")
        self.write("/sys/class/hwmon/hwmon0/fan2_input", "not available")
        self.write("/sys/class/hwmon/hwmon0/fan3_input", "1200")
        self.write("/sys/class/hwmon/hwmon0/fan3_fault", "1")
        self.write("/sys/class/hwmon/hwmon0/fan4_input", "-1")
        fans = self.service.orden(["estado"])["ventiladores"]
        self.assertEqual(fans["alienware_wmi / CPU"], 0)
        self.assertEqual(fans["hwmon1 / alienware_wmi / CPU"], 2500)
        for name in ("fan2", "fan3", "fan4"):
            self.assertIsNone(fans["alienware_wmi / " + name])


if __name__ == "__main__":
    unittest.main(verbosity=2)
