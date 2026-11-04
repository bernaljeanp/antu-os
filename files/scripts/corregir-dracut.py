#!/usr/bin/env python3
"""Backport mínimo de dracut fbb7270edcf9fbc1c60959dc35e532dfe5c382b8.

https://github.com/dracut-ng/dracut/pull/2494
Solo modifica el generador defectuoso conocido; no desactiva el cifrado.
"""
import hashlib
from pathlib import Path

ORIGINAL = "e3b0356432cbda2373e754ecb1f1084f0bb86d06fc5ce770414cffe8332bf458"
CHANGES = (("    return 0\n", "    exit 0\n"),
           ("[ -e /etc/crypttab ] || return 0", "[ -e /etc/crypttab ] || exit 0"),
           ('[ -n "$GENERATOR_DIR" ] || return 1', '[ -n "$GENERATOR_DIR" ] || exit 1'))


def fix(path, expected=ORIGINAL):
    path = Path(path)
    if not path.exists():
        return False
    raw = path.read_bytes(); text = raw.decode()
    if not any(before in text for before, _ in CHANGES):
        return False
    if hashlib.sha256(raw).hexdigest() != expected:
        raise RuntimeError("El generador de dracut cambió: revisar upstream antes de aplicar el parche.")
    for before, after in CHANGES:
        if text.count(before) != 1:
            raise RuntimeError("El generador no coincide con la corrección revisada.")
        text = text.replace(before, after)
    path.write_text(text, newline="\n")
    return True


if __name__ == "__main__":
    changed = fix("/usr/lib/dracut/modules.d/70crypt/crypt-generator.sh")
    print("Generador de cifrado:", "corregido según upstream #2494" if changed else "sin corrección pendiente")
