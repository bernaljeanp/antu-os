"""Comparación de tiempos de cuadro. MangoHud (ms) y PresentMon MsBetweenPresents (ms)."""
import csv
import hashlib
import io
import math
from pathlib import Path
import statistics


def analizar(path):
    path = Path(path)
    if path.stat().st_size > 100 * 1024**2:
        raise ValueError("El registro supera 100 MB. Recorta una sesión antes de compararla.")
    with path.open("rb") as source:
        raw = source.read(100 * 1024**2 + 1)
    if len(raw) > 100 * 1024**2:
        raise ValueError("El registro supera 100 MB.")
    lines = raw.decode("utf-8-sig", errors="replace").splitlines()
    keys = ("frametime", "frametime(ms)", "msbetweenpresents")
    header = next((i for i, line in enumerate(lines[:40]) if any(k in [c.strip().lower().replace(" ", "") for c in next(csv.reader([line]))] for k in keys)), None)
    if header is None:
        raise ValueError("El CSV necesita frametime de MangoHud o MsBetweenPresents de PresentMon, en milisegundos.")
    records = csv.DictReader(io.StringIO("\n".join(lines[header:])))
    field = next(k for k in records.fieldnames if k.strip().lower().replace(" ", "") in keys)
    values, discarded = [], 0
    for record in records:
        try:
            value = float(record[field])
            if not math.isfinite(value) or value <= 0:
                raise ValueError()
            values.append(value)
        except (ValueError, TypeError, KeyError):
            discarded += 1
    if len(values) < 300:
        raise ValueError("Se necesitan al menos 300 cuadros válidos; usa una sesión de varios minutos.")
    ordered = sorted(values)
    worst = ordered[-max(1, math.ceil(len(values) * .01)):]
    def percentile(p):
        return ordered[max(0, math.ceil(len(ordered) * p) - 1)]
    return {"frames": len(values), "discarded": discarded, "seconds": sum(values) / 1000, "source_sha256": hashlib.sha256(raw).hexdigest(),
            "fps": 1000 / statistics.mean(values), "one_percent_low_fps": 1000 / statistics.mean(worst),
            "p95_ms": percentile(.95), "p99_ms": percentile(.99), "frames_over_50_ms": sum(v > 50 for v in values)}


def comparar(first, second, conditions_a, conditions_b):
    if not conditions_a.strip() or conditions_a.strip().casefold() != conditions_b.strip().casefold():
        raise ValueError("Anota las mismas condiciones en ambas sesiones: juego, escena, resolución, calidad, límite de FPS y alimentación.")
    return {"conditions": conditions_a.strip(), "a": analizar(first), "b": analizar(second),
            "method": "FPS=1000/media(ms); 1% bajo=1000/media del 1% de cuadros más lentos; P95/P99 por rango superior. No se descartan tirones."}
