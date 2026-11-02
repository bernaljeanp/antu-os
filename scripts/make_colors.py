"""Genera los esquemas de color de KDE de Antu (Túnel y Andén) desde los tokens del sistema Metro.

Uso: python scripts/make_colors.py   (luego: python scripts/check_colors.py)
"""
import pathlib

OUT = pathlib.Path(__file__).parent.parent / "files/system/usr/share/color-schemes"

# Selección: la línea Sistema (azul) con texto blanco; igual en ambos esquemas.
SELECTION = dict(bg="#1450A0", alt="#0F4288", fg="#FFFFFF", inactive="#D6E2FA", link="#FFFFFF",
                 visited="#E3DCFF", negative="#FFD2CD", neutral="#FFE3A3", positive="#C9F2DA")

TUNEL = dict(  # noche: grafito de túnel, por defecto
    name="Antu Túnel", id="AntuTunel",
    window=("#141517", "#1A1B1E"), view=("#1E2023", "#24272B"), button=("#26292E", "#2C3036"),
    header=("#0F1012", "#141517"), tooltip=("#26292E", "#1E2023"),
    fg="#F2F1EC", inactive="#A9ABA6", focus="#4F86E8", active="#6E9BF0", link="#7FA8F5",
    visited="#A99BF0", negative="#FF6B5E", neutral="#E9A800", positive="#3CC27A",
)
ANDEN = dict(  # día: esmalte de andén
    name="Antu Andén", id="AntuAnden",
    window=("#F7F6F2", "#EFEDE7"), view=("#FFFFFF", "#F4F3EF"), button=("#FFFFFF", "#EFEDE7"),
    header=("#EFEDE7", "#E7E5DE"), tooltip=("#FFFFFF", "#F4F3EF"),
    fg="#1C1C1B", inactive="#5E5F5B", focus="#1450A0", active="#1450A0", link="#1450A0",
    visited="#4A3AA0", negative="#B3221A", neutral="#8A5A00", positive="#0B6E39",
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
    # Complementary (paneles oscuros) usa siempre el Túnel, también en el esquema de día.
    groups["Complementary"] = group(*TUNEL["header"], **{k: TUNEL[k] for k in text})
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
    for t in (TUNEL, ANDEN):
        path = OUT / f"{t['id']}.colors"
        path.write_text(scheme(t), encoding="utf-8", newline="\n")
        print("escrito", path.name)
