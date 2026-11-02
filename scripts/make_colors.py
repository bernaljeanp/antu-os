"""Genera los esquemas de color de KDE de Antu (Obsidiana y Salar): macOS en versión gamer, un solo acento de lava.

Uso: python scripts/make_colors.py   (luego: python scripts/check_colors.py)
"""
import pathlib

OUT = pathlib.Path(__file__).parent.parent / "files/system/usr/share/color-schemes"

# Selección: lava oscurecida para que el texto blanco cumpla 4.5:1; igual en ambos esquemas.
SELECTION = dict(bg="#C93A0C", alt="#B0320A", fg="#FFFFFF", inactive="#FFF1EA", link="#FFFFFF",
                 visited="#F6EEFF", negative="#FFF0EF", neutral="#FFF6DB", positive="#EFFFF2")

OBSIDIANA = dict(  # noche: vidrio volcánico, por defecto
    name="Antu Obsidiana", id="AntuObsidiana",
    window=("#1C1C21", "#222228"), view=("#16161A", "#1C1C21"), button=("#2A2A31", "#303038"),
    header=("#141418", "#1A1A1F"), tooltip=("#2A2A31", "#222228"),
    fg="#F5F5F7", inactive="#A1A1A6", focus="#FF5A1F", active="#FF7A45", link="#FF8A5C",
    visited="#C9A0FF", negative="#FF7069", neutral="#FFBD2E", positive="#28C840",
)
SALAR = dict(  # día: blanco de salar
    name="Antu Salar", id="AntuSalar",
    window=("#F5F5F7", "#EDEDF0"), view=("#FFFFFF", "#F7F7F9"), button=("#FFFFFF", "#EDEDF0"),
    header=("#ECECEF", "#E4E4E8"), tooltip=("#FFFFFF", "#F7F7F9"),
    fg="#1D1D1F", inactive="#5E5E64", focus="#E2480F", active="#C93A0C", link="#B5340A",
    visited="#6B3FA0", negative="#B8251A", neutral="#8A5A00", positive="#0B6E39",
)


def rgb(hex_color):
    h = hex_color.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def group(bg, alt, fg, inactive, focus, active, link, visited, negative, neutral, positive):
    return {
        "BackgroundAlternate": alt, "BackgroundNormal": bg,
        "DecorationFocus": focus, "DecorationHover": focus,
        "ForegroundActive": active, "ForegroundInactive": inactive, "ForegroundLink": link,
        "ForegroundNegative": negative, "ForegroundNeutral": neutral, "ForegroundNormal": fg,
        "ForegroundPositive": positive, "ForegroundVisited": visited,
    }


def scheme(t):
    text = {k: t[k] for k in ("fg", "inactive", "focus", "active", "link", "visited", "negative", "neutral", "positive")}
    groups = {name: group(*t[key], **text) for name, key in
              [("Button", "button"), ("Header", "header"), ("Tooltip", "tooltip"), ("View", "view"), ("Window", "window")]}
    # Complementary (paneles oscuros) usa siempre Obsidiana, también en el esquema de día.
    groups["Complementary"] = group(*OBSIDIANA["header"], **{k: OBSIDIANA[k] for k in text})
    s = SELECTION
    groups["Selection"] = group(s["bg"], s["alt"], s["fg"], s["inactive"], t["focus"], s["fg"], s["link"],
                                s["visited"], s["negative"], s["neutral"], s["positive"])

    lines = []
    for effect, color in (("Disabled", t["window"][0]), ("Inactive", t["window"][0])):
        lines += [f"[ColorEffects:{effect}]", f"Color={rgb(color)}"]
        lines += (["ColorAmount=0", "ColorEffect=0", "ContrastAmount=0.65", "ContrastEffect=1",
                   "IntensityAmount=0.1", "IntensityEffect=2"] if effect == "Disabled" else
                  ["ChangeSelectionColor=true", "ColorAmount=0.025", "ColorEffect=2", "ContrastAmount=0.1",
                   "ContrastEffect=2", "Enable=false", "IntensityAmount=0", "IntensityEffect=0"])
        lines.append("")
    for name in sorted(groups):
        lines.append(f"[Colors:{name}]")
        lines += [f"{k}={rgb(v)}" for k, v in sorted(groups[name].items())]
        lines.append("")
    hdr = t["header"][0]
    lines += ["[General]", f"ColorScheme={t['id']}", f"Name={t['name']}", "shadeSortColumn=true", "",
              "[KDE]", "contrast=4", "",
              "[WM]", f"activeBackground={rgb(hdr)}", f"activeBlend={rgb(hdr)}", f"activeForeground={rgb(t['fg'])}",
              f"inactiveBackground={rgb(t['window'][0])}", f"inactiveBlend={rgb(t['window'][0])}",
              f"inactiveForeground={rgb(t['inactive'])}", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    for t in (OBSIDIANA, SALAR):
        path = OUT / f"{t['id']}.colors"
        path.write_text(scheme(t), encoding="utf-8", newline="\n")
        print("escrito", path.name)
