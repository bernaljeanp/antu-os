"""Estilo original de controles Qt de Antu, sin copiar dibujos de otros temas.

Kvantum es solo el motor. Estas piezas geométricas y configuraciones son de Antu OS (GPL-3.0-or-later).
python scripts/make_widget_theme.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "files/system/usr/share/Kvantum"
STATES = ("normal", "focused", "pressed", "toggled", "disabled")


def build(name, dark):
    bg, face, low, edge, text = (("#1C1C21", "#34343C", "#25252D", "#666671", "#F5F5F7") if dark
                                else ("#F5F5F7", "#FFFFFF", "#EDEDF1", "#9696A0", "#1D1D1F"))
    base = "#16161A" if dark else "#FFFFFF"
    muted = "#A1A1A6" if dark else "#5E5E64"
    lava = "#FF783D" if dark else "#AE330C"
    pieces, definitions = [], []
    atlas_y = 0

    def element(ident, shape):
        pieces.append(f'<g id="{ident}" transform="translate(0 {atlas_y})">{shape}</g>')

    def panel(family, state, top, bottom, outline):
        nonlocal atlas_y
        g = f"{family}-{state}-fill"
        definitions.append(f'<linearGradient id="{g}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="48"><stop stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient>')
        fill = f'fill="url(#{g})"'
        prefix = f"{family}-{state}"
        element(prefix, f'<rect x="8" y="8" width="32" height="32" {fill}/>' )
        sides = {"top": (8,0,32,8), "bottom": (8,40,32,8), "left": (0,8,8,32), "right": (40,8,8,32)}
        lines = {"top": (8,0,32,1), "bottom": (8,47,32,1), "left": (0,8,1,32), "right": (47,8,1,32)}
        for side,(x,y,w,h) in sides.items():
            a,b,c,d = lines[side]
            element(prefix+'-'+side, f'<rect x="{x}" y="{y}" width="{w}" height="{h}" {fill}/><rect x="{a}" y="{b}" width="{c}" height="{d}" fill="{outline}"/>')
        corners = {
            "topleft": ('M8,0 A8,8 0 0 0 0,8 L8,8 Z','M8,0 A8,8 0 0 0 0,8 L1,8 A7,7 0 0 1 8,1 Z'),
            "topright": ('M40,0 A8,8 0 0 1 48,8 L40,8 Z','M40,0 A8,8 0 0 1 48,8 L47,8 A7,7 0 0 0 40,1 Z'),
            "bottomleft": ('M0,40 A8,8 0 0 0 8,48 L8,40 Z','M0,40 A8,8 0 0 0 8,48 L8,47 A7,7 0 0 1 1,40 Z'),
            "bottomright": ('M48,40 A8,8 0 0 1 40,48 L40,40 Z','M48,40 A8,8 0 0 1 40,48 L40,47 A7,7 0 0 0 47,40 Z'),
        }
        for side,(body,border) in corners.items():
            element(prefix+'-'+side, f'<path d="{body}" {fill}/><path d="{border}" fill="{outline}"/>')
        atlas_y += 54

    for family in ("button", "field", "menu", "header", "item", "tab", "scroll", "progress", "focus", "toolbar"):
        for state in STATES:
            top, bottom, outline = face, low, edge
            if family in ("field", "menu"):
                top, bottom = base, bg
            if family in ("header", "toolbar"):
                top, bottom = face, bg
            if state == "focused":
                outline = lava
            if state in ("pressed", "toggled"):
                top, bottom, outline = "#C44317", "#A62E0B", "#E76A35"
            if family == "progress":
                top, bottom, outline = "#C44317", "#A62E0B", lava
            if state == "disabled":
                top, bottom, outline = bg, bg, "#45454E" if dark else "#CDCDD3"
            if family == "focus":
                outline = "#FFFFFF" if dark else "#24242B"
            panel(family,state,top,bottom,outline)

    # Indicadores funcionales originales: no se sustituyen los iconos de acciones del sistema.
    for state in STATES:
        for checked in (False, True):
            ident = "checkbox-" + ("checked-" if checked else "") + state
            outline = lava if state != "disabled" else muted
            fill = "#B3340D" if checked else base
            shape = f'<rect x="1" y="1" width="18" height="18" rx="4" fill="{fill}" stroke="{outline}" stroke-width="1.5"/>'
            if checked:
                shape += '<path d="M5,10 L8.5,13.5 L15,6.5" fill="none" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
            element(ident,shape)
            atlas_y += 26
            element("radio-" + ("checked-" if checked else "") + state,
                    f'<circle cx="10" cy="10" r="8.5" fill="{base}" stroke="{outline}" stroke-width="1.5"/>' +
                    (f'<circle cx="10" cy="10" r="4.5" fill="{lava}"/>' if checked else ""))
            atlas_y += 26
        for direction,path in (("down","M4,7 L10,13 L16,7"),("up","M4,13 L10,7 L16,13"),
                               ("left","M13,4 L7,10 L13,16"),("right","M7,4 L13,10 L7,16")):
            element(f"arrow-{direction}-{state}",f'<path d="{path}" fill="none" stroke="{muted if state=="disabled" else text}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
            atlas_y += 26

    sections = ["[%General]\nauthor=Antu OS\ncomment=Grafito mate, canto satinado y acentos lava. Arte original.\nrespect_DE=true\ncomposite=false\ntranslucent_windows=false\nblurring=false\npopup_blurring=false\nremove_extra_frames=true\nsmall_icon_size=22\nlarge_icon_size=32\nscrollbar_width=12\ncheck_size=20\nradio_size=20\nlayout_spacing=8\nlayout_margin=12\nbutton_contents_shift=true\nbutton_default_indicator=true\ncombo_focus_rect=true\nx11drag=menubar_and_primary_toolbar\n",
                f"[GeneralColors]\nwindow.color={bg}\nbase.color={base}\nalt.base.color={low}\nbutton.color={face}\ntext.color={text}\nwindow.text.color={text}\nbutton.text.color={text}\ndisabled.text.color={muted}\nhighlight.color=#B3340D\nhighlight.text.color=#FFFFFF\nlink.color={lava}\ntooltip.base.color={face}\ntooltip.text.color={text}\n"]
    mapping = {"PanelButtonCommand":"button","PanelButtonTool":"button","LineEdit":"field","ComboBox":"field",
               "Menu":"menu","ToolTip":"menu","HeaderSection":"header","Toolbar":"toolbar","MenuBar":"toolbar",
               "MenuItem":"item","ItemView":"item","Tab":"tab","ScrollbarGroove":"field","ScrollbarSlider":"scroll",
               "Slider":"field","SliderCursor":"scroll","Progressbar":"field","ProgressbarContents":"progress",
               "Focus":"focus","GenericFrame":"field","TabFrame":"field","GroupBox":"field"}
    for section, family in mapping.items():
        sections.append(f"[{section}]\nframe=true\nframe.element={family}\nframe.top=8\nframe.bottom=8\nframe.left=8\nframe.right=8\ninterior={'false' if section=='Focus' else 'true'}\ninterior.element={family}\ntext.margin.top=4\ntext.margin.bottom=4\ntext.margin.left=8\ntext.margin.right=8\ntext.normal.color={text}\ntext.focus.color={text}\ntext.press.color=#FFFFFF\ntext.toggle.color=#FFFFFF\ntext.shadow=false\nindicator.element=arrow\nindicator.size=16\n")
    # La estructura de una ventana queda mate y abierta: no se enmarca cada lista o barra como un botón.
    for i, section in enumerate(sections):
        if any(section.startswith('['+name+']') for name in ('GenericFrame','ItemView','TabFrame','MenuBar','Toolbar')):
            sections[i] = section.replace('frame=true', 'frame=false').replace('interior=true', 'interior=false')
    sections += ["[CheckBox]\nindicator.element=checkbox\nindicator.size=20\ntext.spacing=8\n",
                 "[RadioButton]\nindicator.element=radio\nindicator.size=20\ntext.spacing=8\n",
                 "[Hacks]\ntransparent_dolphin_view=false\ntransparent_pcmanfm_view=false\n"]
    folder = DEST/name
    folder.mkdir(parents=True,exist_ok=True)
    (folder/f"{name}.kvconfig").write_text("\n".join(sections),encoding="utf-8",newline="\n")
    (folder/f"{name}.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="{atlas_y}" viewBox="0 0 64 {atlas_y}">\n<metadata>Original Antu OS artwork. SPDX-License-Identifier: CC-BY-SA-4.0</metadata>\n<defs>'+"\n".join(definitions)+"</defs>\n"+"\n".join(pieces)+"\n</svg>\n",encoding="utf-8",newline="\n")


if __name__ == "__main__":
    build("AntuObsidiana",True)
    build("AntuSalar",False)
    print("Dos estilos Qt originales escritos; los iconos de acciones siguen en su tema nativo.")
