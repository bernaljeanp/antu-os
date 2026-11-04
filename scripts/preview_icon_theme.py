"""Review proofs for Antu icons. Never changes installed artwork.

Native-size contact sheets plus an original Dolphin mockup made from the actual
theme PNGs. The mockup is a review illustration, not a screenshot of a live KDE session.
"""
import math
from pathlib import Path
import textwrap

from PIL import Image,ImageDraw,ImageFilter,ImageFont

from antu_icon_catalog import CATALOG

ROOT=Path(__file__).resolve().parent.parent
THEME=ROOT/"files/system/usr/share/icons/Antu"
OUT=ROOT/"brand/previews/icon-theme"
FONT=ROOT/"files/system/usr/share/fonts/antu/Inter-Variable.ttf"
BG="#0B0B0E"
INK="#F5F5F7"
SECONDARY="#C7C7CC"
LAVA="#FF5A1F"


def font(size,weight=500):
    f=ImageFont.truetype(str(FONT),size)
    f.set_variation_by_axes([14,weight])
    return f


def icon(context,name,size):
    return Image.open(THEME/f"{size}x{size}"/context/f"{name}.png").convert("RGBA")


def put(out,context,name,size,x,y):
    image=icon(context,name,size)
    out.paste(image,(int(x),int(y)),image)


def sheet(items,title,filename):
    columns=7 if len(items)>20 else 5;cw=3840/columns;rh=490
    rows=math.ceil(len(items)/columns)
    out=Image.new("RGB",(3840,2160),"#1C1C21")
    d=ImageDraw.Draw(out)
    d.text((34,27),title,font=font(34,600),fill=INK)
    d.text((34,82),"Recursos finales · 16 / 32 / 64 / 256 px · todos a tamaño real (1:1)",font=font(22),fill=SECONDARY)
    for i,(context,name) in enumerate(items):
        x=(i%columns)*cw+32;y=150+(i//columns)*rh
        label=textwrap.fill(name,27,break_long_words=True,break_on_hyphens=True)
        d.multiline_text((x,y),label,font=font(18),fill=INK,spacing=4)
        for size,dx in [(16,0),(32,65),(64,151)]:
            put(out,context,name,size,x+dx,y+85)
            d.text((x+dx,y+153),str(size),font=font(16),fill=SECONDARY)
        put(out,context,name,256,x+100,y+200)
        d.text((x,y+460),"256 px",font=font(16),fill=SECONDARY)
    out.save(OUT/filename,optimize=True)


def small_sizes():
    items=[(c,n) for c,v in CATALOG.items() for n in v]
    cols=3;rows=math.ceil(len(items)/cols);cw=1280;rh=92
    out=Image.new("RGB",(3840,2160),"#1C1C21");d=ImageDraw.Draw(out)
    d.text((28,20),"ANTU / LECTURA PEQUEÑA",font=font(31,600),fill=INK)
    for col in range(cols):
        for n,x in zip((16,22,24,32),(780,880,980,1080)):
            d.text((col*cw+x,83),str(n)+" px",font=font(18),fill=SECONDARY)
    for i,(context,name) in enumerate(items):
        col=i//rows;row=i%rows;x=col*cw+28;y=130+row*rh
        if row%2==0:d.rectangle((x-8,y-5,x+1220,y+rh-7),fill="#111115")
        d.text((x,y+8),name,font=font(19),fill=INK)
        for n,dx in zip((16,22,24,32),(780,880,980,1080)):
            put(out,context,name,n,col*cw+dx,y+8+(32-n)//2)
    out.save(OUT/"small-sizes.png",optimize=True)
    # Transparent PNGs are also legible over a light file-manager pane.
    compact=Image.new("RGB",(3840,2160),"#F5F5F7");cd=ImageDraw.Draw(compact)
    cd.text((48,36),"ANTU / FONDO CLARO · recursos a tamaño real",font=font(38,600),fill=BG)
    names=[("places",n) for n in ["folder","folder-open","user-home","folder-documents","folder-download","folder-pictures","folder-games","user-trash","network-workgroup","start-here"]]+[("devices","drive-harddisk-solidstate"),("mimetypes","text-plain")]
    for i,(context,name) in enumerate(names):
        x=48+(i%4)*960;y=160+(i//4)*650
        cd.text((x,y),name,font=font(26),fill=BG)
        for size,dx in [(16,0),(32,100),(64,220),(256,390)]:
            put(compact,context,name,size,x+dx,y+110)
            cd.text((x+dx,y+395),str(size)+" px",font=font(22),fill=BG)
    compact.save(OUT/"light-background-check.png",optimize=True)


def glass(out,rect,radius=26,darkness=0.86):
    mask=Image.new("L",out.size)
    ImageDraw.Draw(mask).rounded_rectangle(rect,radius,fill=255)
    # La ventana real es grafito opaco; el fondo de pantalla no sustituye su superficie.
    out.paste(Image.new("RGB",out.size,"#1C1C21"),(0,0),mask)
    ImageDraw.Draw(out).rounded_rectangle(rect,radius,outline="#48484D",width=2)


def dolphin():
    out=Image.open(ROOT/"files/system/usr/share/wallpapers/Antu/contents/images_dark/3840x2160.jpg").convert("RGB")
    d=ImageDraw.Draw(out)
    d.text((96,60),"Antu · Dolphin",font=font(58,600),fill=INK)
    d.text((98,145),"Carpetas con cuerpo de obsidiana y grabados de plata. El acento lava señala Juegos.",font=font(29),fill=SECONDARY)
    windows=[(96,260,1870,1960),(1960,260,3744,1960)]
    labels=[("user-home","Carpeta personal"),("user-desktop","Escritorio"),("folder-documents","Documentos"),
            ("folder-download","Descargas"),("folder-pictures","Imágenes"),("folder-music","Música"),
            ("folder-videos","Vídeos"),("folder-games","Juegos"),("folder-templates","Plantillas"),
            ("folder-publicshare","Público"),("folder-remote","Remoto"),("user-trash","Papelera")]
    for mode,(x0,y0,x1,y1) in enumerate(windows):
        glass(out,(x0,y0,x1,y1),28,0.88)
        d=ImageDraw.Draw(out)
        d.text((x0+36,y0+30),"Carpeta personal — Dolphin",font=font(31,600),fill=INK)
        for i,col in enumerate(("#57575E","#57575E",LAVA)):
            cx=x1-160+i*50
            d.ellipse((cx,y0+36,cx+23,y0+59),fill=col)
        d.line((x0+1,y0+94,x1-1,y0+94),fill="#35353A",width=2)
        d.text((x0+36,y0+126),"‹     ›",font=font(36),fill=SECONDARY)
        d.rounded_rectangle((x0+200,y0+113,x1-35,y0+171),13,fill="#232329",outline="#404047")
        put(out,"places","user-home",32,x0+219,y0+126)
        d.text((x0+270,y0+127),"Carpeta personal",font=font(27),fill=INK)
        d.line((x0+315,y0+200,x0+315,y1-62),fill="#36363C",width=2)
        d.text((x0+30,y0+218),"Lugares",font=font(25,600),fill=SECONDARY)
        for row,(name,label) in enumerate(labels[:8]):
            yy=y0+276+row*72
            if row==0:d.rounded_rectangle((x0+15,yy-8,x0+298,yy+51),12,fill="#303036")
            put(out,"places",name,32,x0+33,yy+5)
            d.text((x0+82,yy+5),label,font=font(23),fill=INK)
        if mode==0:
            content_x=x0+342
            for i,(name,label) in enumerate(labels):
                col=i%4;row=i//4
                xx=content_x+col*350;yy=y0+270+row*425
                if name=="folder-games":
                    d.rounded_rectangle((xx+3,yy-13,xx+318,yy+335),18,fill="#2D211C",outline="#7F452E",width=2)
                put(out,"places",name,256,xx+29,yy)
                bb=d.textbbox((0,0),label,font=font(25))
                d.text((xx+157-(bb[2]-bb[0])/2,yy+280),label,font=font(25),fill=INK)
        else:
            xx=x0+350;header_y=y0+230
            for tx,label in [(xx,"Nombre"),(xx+660,"Modificado"),(xx+1110,"Tipo")]:
                d.text((tx,header_y),label,font=font(24,600),fill=SECONDARY)
            d.line((xx-10,header_y+46,x1-26,header_y+46),fill="#3B3B41",width=2)
            for row,(name,label) in enumerate(labels):
                yy=y0+310+row*89
                if row%2==0:d.rounded_rectangle((xx-12,yy-15,x1-28,yy+58),8,fill="#1B1B20")
                if name=="folder-games":d.rounded_rectangle((xx-12,yy-15,x1-28,yy+58),8,fill="#33251E",outline="#74432F")
                put(out,"places",name,32,xx,yy+3)
                d.text((xx+58,yy+4),label,font=font(26),fill=INK)
                d.text((xx+660,yy+6),"Hoy, 09:30",font=font(23),fill=SECONDARY)
                d.text((xx+1110,yy+6),"Carpeta",font=font(23),fill=SECONDARY)
        d.line((x0+1,y1-62,x1-1,y1-62),fill="#38383E",width=2)
        d.text((x0+34,y1-44),"12 elementos",font=font(23),fill=SECONDARY)
        d.text((x1-340,y1-44),"Vista de íconos" if mode==0 else "Vista de detalles",font=font(23),fill=SECONDARY)
    d=ImageDraw.Draw(out)
    d.text((98,2025),"Maqueta de revisión · íconos de 256 px",font=font(26),fill=INK)
    d.text((1960,2025),"Lista de 32 px · recursos pegados sin ampliar",font=font(26),fill=INK)
    d.text((98,2090),"ANTU / OBSIDIANA · PLATA · LAVA",font=font(20,600),fill=SECONDARY)
    out.save(OUT/"dolphin-mockup-4k.png",optimize=True)


def create_previews():
    OUT.mkdir(parents=True,exist_ok=True)
    sheet([("places",n) for n in CATALOG["places"]],"ANTU / CARPETAS Y LUGARES","places.png")
    sheet([("mimetypes",n) for n in CATALOG["mimetypes"]],"ANTU / TIPOS DE ARCHIVO","mimetypes.png")
    sheet([(c,n) for c in ("devices","apps") for n in CATALOG[c]],"ANTU / DISPOSITIVOS Y APLICACIONES","devices-apps.png")
    small_sizes()
    dolphin()
    print("Review sheets, optical-size proof and native 4K Dolphin mockup written outside files/.")


if __name__=="__main__":create_previews()
