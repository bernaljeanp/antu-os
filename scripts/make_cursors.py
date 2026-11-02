"""Antu Cursores, opción Punta: geometría 2D original. CC-BY-SA-4.0.
La maqueta aprobada fija la silueta, la obsidiana, el blanco y el filo interior.
Cada tamaño se dibuja desde geometría propia con Pillow y supermuestreo.
"""
import argparse
import collections
import configparser
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import struct

RAIZ = Path(__file__).resolve().parent.parent
MAESTROS = RAIZ / 'brand/masters/cursors'
TAMANOS = (24, 32, 36, 48, 64, 72, 96)
FORMAS = ('default', 'pointer', 'openhand', 'closedhand', 'text', 'vertical-text',
          'crosshair', 'help', 'not-allowed', 'copy', 'link', 'context-menu', 'cell', 'fleur',
          'top_side', 'bottom_side', 'left_side', 'right_side', 'top_left_corner',
          'top_right_corner', 'bottom_left_corner', 'bottom_right_corner',
          'size_hor', 'size_ver', 'size_bdiag', 'size_fdiag', 'col-resize', 'row-resize',
          'zoom-in', 'zoom-out', 'pencil', 'color-picker', 'wait', 'progress')
# Grosor físico del contorno; 24/32 tienen compensación y encaje propios.
OPTICA = {24: (1.45, 12), 32: (1.80, 12), 36: (1.97, 8), 48: (2.625, 8),
          64: (3.50, 8), 72: (3.9375, 8), 96: (5.25, 8)}
OBSIDIANA = (17, 17, 21, 255)
BLANCO = (255, 255, 255, 255)
MINIMO_CONTRASTE = {24: 40, 32: 72}


def receta(nombre, n):
    """Contrato de puntos activos de la entrega anterior, sin cambiar nombres."""
    k = n / 32
    activo = (n // 2, n // 2)
    if nombre in ('default', 'help', 'copy', 'link', 'context-menu', 'progress'):
        activo = (round(4*k), round(3*k))
    elif nombre == 'pointer':
        activo = (round(12*k), round(3*k))
    elif nombre in ('pencil', 'color-picker'):
        activo = (round(5*k), round(27*k))
    elif nombre in ('zoom-in', 'zoom-out'):
        activo = (round(13.5*k), round(13.5*k))
    return dict(activo=activo, borde=OPTICA[n][0], supermuestreo=OPTICA[n][1])


def desplazar(im, dx, dy):
    """Traslación sin envolver píxeles por el lado opuesto del lienzo."""
    from PIL import Image
    salida = Image.new(im.mode, im.size)
    salida.paste(im, (round(dx), round(dy)))
    return salida


class Dibujo:
    """Máscaras en rejilla de 32 unidades, rasterizadas al tamaño de destino."""
    def __init__(self, n):
        from PIL import Image, ImageDraw
        self.n = n
        self.ss = OPTICA[n][1]
        self.k = n*self.ss/32
        self.m = Image.new('L', (n*self.ss, n*self.ss))
        self.d = ImageDraw.Draw(self.m)

    def caja(self, x0, y0, x1, y1, radio):
        self.d.rounded_rectangle(tuple(v*self.k for v in (x0,y0,x1,y1)),
                                 radius=radio*self.k, fill=255)

    def disco(self, x, y, r, color=255):
        self.d.ellipse(tuple(v*self.k for v in (x-r,y-r,x+r,y+r)), fill=color)

    def trazo(self, pts, ancho):
        self.d.line([(x*self.k,y*self.k) for x,y in pts], fill=255,
                    width=round(ancho*self.k), joint='curve')
        for x,y in pts:
            self.disco(x,y,ancho/2)

    def poligono(self, pts, radio=0.8):
        from PIL import Image, ImageDraw, ImageChops, ImageFilter
        m = Image.new('L', self.m.size)
        ImageDraw.Draw(m).polygon([(x*self.k,y*self.k) for x,y in pts], fill=255)
        if radio:
            m = m.filter(ImageFilter.GaussianBlur(radio*self.k)).point(lambda v: 255 if v>127 else 0)
        self.m = ImageChops.lighter(self.m,m)
        self.d = ImageDraw.Draw(self.m)

    def aro(self, x, y, radio, ancho):
        from PIL import ImageChops
        otro = Dibujo(self.n)
        otro.disco(x,y,radio+ancho/2)
        otro.disco(x,y,radio-ancho/2,0)
        self.m = ImageChops.lighter(self.m,otro.m)
        from PIL import ImageDraw
        self.d = ImageDraw.Draw(self.m)


def exterior_de(forma, borde, ss):
    from PIL import ImageFilter
    # Dilatación redonda. El factor da aproximadamente el grosor físico pedido.
    return forma.filter(ImageFilter.GaussianBlur(borde*ss*0.76)).point(lambda v: 255 if v>24 else 0)


def sombra_de(exterior, n):
    from PIL import Image, ImageFilter
    ss = OPTICA[n][1]
    sombra = Image.new('RGBA', exterior.size)
    from PIL import ImageDraw, ImageChops
    alfa=desplazar(exterior,0,1.3*n/32*ss).filter(ImageFilter.GaussianBlur(2.1*n/32*ss)).point(lambda v: round(v*0.5))
    # La sombra se extingue en el margen del lienzo, sin un recorte rectangular.
    margen=Image.new('L',exterior.size,255);d=ImageDraw.Draw(margen)
    ancho=max(1,round(1.5*n/32*ss));lado=exterior.width
    for i in range(ancho):
        d.rectangle((i,i,lado-1-i,lado-1-i),outline=round(255*i/ancho))
    sombra.putalpha(ImageChops.multiply(alfa,margen))
    return sombra


@lru_cache(maxsize=7)
def degradado_lava(n):
    from PIL import Image, ImageDraw
    lado=n*OPTICA[n][1]
    im=Image.new('RGBA',(lado,lado))
    d=ImageDraw.Draw(im)
    for y in range(lado):
        t=y/max(1,lado-1)
        d.line((0,y,lado,y),fill=(255,round(150-60*t),round(60-29*t),255))
    return im


def filo(forma, n, dx=2.4, dy=-0.2, limite=None):
    """Resta desplazada como la maqueta: una grieta y halo recortados al cuerpo."""
    from PIL import Image, ImageDraw, ImageChops, ImageFilter
    k=n/32*OPTICA[n][1]
    grieta=ImageChops.subtract(forma,desplazar(forma,dx*k,dy*k))
    if limite is not None:
        recorte=Image.new('L',forma.size)
        ImageDraw.Draw(recorte).rectangle(tuple(v*k for v in limite),fill=255)
        grieta=ImageChops.multiply(grieta,recorte)
    # Extremos apagados; el centro conserva el ancho de la maqueta.
    caja=grieta.getbbox()
    if caja:
        apagado=Image.new('L',forma.size)
        d=ImageDraw.Draw(apagado)
        for y in range(caja[1],caja[3]):
            t=(y-caja[1]+0.5)/(caja[3]-caja[1])
            d.line((0,y,forma.width,y),fill=round(255*min(1,t/0.12,(1-t)/0.12)**0.65))
        grieta=ImageChops.multiply(grieta,apagado)
    grieta=grieta.filter(ImageFilter.GaussianBlur(0.18*k))
    halo=grieta.filter(ImageFilter.GaussianBlur(1.3*k)).point(lambda v: round(v*0.65))
    return ImageChops.multiply(ImageChops.lighter(grieta,halo),forma)


def obsidiana_con_filo(forma,n,dx=2.4,dy=-0.2,limite=None,lava=True,borde=None):
    from PIL import Image
    exterior=exterior_de(forma, borde or OPTICA[n][0], OPTICA[n][1])
    capa=sombra_de(exterior,n)
    blanco=Image.new('RGBA',forma.size,BLANCO);blanco.putalpha(exterior)
    capa.alpha_composite(blanco)
    cuerpo=Image.new('RGBA',forma.size,OBSIDIANA);cuerpo.putalpha(forma)
    capa.alpha_composite(cuerpo)
    if lava:
        luz=degradado_lava(n).copy();luz.putalpha(filo(forma,n,dx,dy,limite))
        capa.alpha_composite(luz)
    return capa


def punta(n, escala=1):
    """Los cuatro vértices y el redondeo aprobados, sin cola añadida."""
    from PIL import ImageDraw
    d=Dibujo(n)
    d.poligono([(x*escala,y*escala) for x,y in
                ((4.6,3.6),(11.2,28.6),(15.2,18.6),(27.2,13.4))],1.05*escala)
    exterior=exterior_de(d.m,OPTICA[n][0],d.ss)
    x0,y0,x1,y1=exterior.getbbox()
    # El extremo superior visible se coloca dentro de su celda activa exacta.
    fila=exterior.crop((0,y0,exterior.width,y0+1)).getbbox()
    cx=(fila[0]+fila[2])/2
    hx,hy=receta('default',n)['activo']
    d.m=desplazar(d.m,(hx+0.5)*d.ss-cx,(hy+0.04)*d.ss-y0)
    d.d=ImageDraw.Draw(d.m)
    return d


def centrar(d,activo=None):
    hx,hy=activo or receta('crosshair',d.n)['activo']
    return desplazar(d.m,(hx+0.5)*d.ss-16*d.k,(hy+0.5)*d.ss-16*d.k)


def geometria(nombre,n):
    """Familia nueva de siluetas; no depende de imágenes de la entrega anterior."""
    d=Dibujo(n)
    if nombre in ('default','help','copy','link','context-menu','progress'):
        return punta(n, 0.70 if nombre=='progress' else (0.78 if nombre!='default' else 1)).m
    if nombre=='pointer':
        d.caja(10.5,2.4,15.0,20.5,2.25)
        d.caja(14.5,10.7,19.1,22,2.3)
        d.caja(18.5,12.0,23,22,2.25)
        d.caja(22.2,13.8,26.6,22.5,2.2)
        d.caja(10.5,16,26.6,28.0,4.4)
        d.trazo([(6.5,16.9),(11.1,23.8),(15.1,26.2)],5.0)
        hx,hy=receta(nombre,n)['activo']
        return desplazar(d.m,(hx+0.5)*d.ss-12.75*d.k,(hy+0.5)*d.ss-2.4*d.k)
    if nombre=='openhand':
        d.caja(9,16.5,26,28,4.4)
        d.trazo([(9.8,18),(8.4,8)],3.8)
        d.trazo([(14.7,18),(14.2,4.2)],3.8)
        d.trazo([(19.4,18),(20.2,5.8)],3.8)
        d.trazo([(23,20),(25.2,10.3)],3.7)
        d.trazo([(11.6,24),(6.1,17)],4.8)
    elif nombre=='closedhand':
        d.caja(7.5,13,26.7,27.6,5.2)
        for x,y in ((9.9,10.4),(14.2,8.5),(18.5,9),(22.5,11)):
            d.caja(x-2.3,y,x+2.3,21,2.3)
        d.trazo([(6.7,17),(10.3,23)],4.7)
    elif nombre in ('text','vertical-text'):
        # Cuerpo central macizo: 3.5 px a 24, antes del blanco exterior.
        d.caja(13.7,5,18.3,27,2.1)
        d.caja(10.2,3.8,21.8,7.6,1.9)
        d.caja(10.2,24.4,21.8,28.2,1.9)
        if nombre=='vertical-text':
            from PIL import Image
            d.m=d.m.transpose(Image.Transpose.ROTATE_90)
    elif nombre=='crosshair':
        d.trazo([(5.2,16),(26.8,16)],4.4)
        d.trazo([(16,5.2),(16,26.8)],4.4)
    elif nombre=='cell':
        # Hueco útil de 4 unidades después del contorno, sin filigrana.
        for pts in ([(4.7,16),(10.5,16)],[(21.5,16),(27.3,16)],
                    [(16,4.7),(16,10.5)],[(16,21.5),(16,27.3)]):
            d.trazo(pts,3.8)
        d.trazo([(10,10),(22,10),(22,22),(10,22),(10,10)],3.2)
    elif nombre=='not-allowed':
        d.aro(16,16,9.6,4.6)
        d.trazo([(9.3,9.3),(22.7,22.7)],4.6)
    elif nombre=='fleur':
        d.trazo([(16,7),(16,25)],5.8)
        d.trazo([(7,16),(25,16)],5.8)
        for pts in ([(16,3.3),(22,10.2),(10,10.2)],[(28.7,16),(21.8,22),(21.8,10)],
                    [(16,28.7),(10,21.8),(22,21.8)],[(3.3,16),(10.2,10),(10.2,22)]):
            d.poligono(pts,0.9)
    elif nombre in ('zoom-in','zoom-out'):
        hx,hy=receta(nombre,n)['activo']
        cx,cy=(hx+0.5)*32/n,(hy+0.5)*32/n
        d.disco(cx,cy,8.0)
        d.trazo([(cx+5.9,cy+5.9),(27.1,27.1)],5.3)
        return d.m
    elif nombre=='pencil':
        d.poligono([(5,27),(7.5,18.8),(21.6,4.8),(27.2,10.4),(13.1,24.5)],0.65)
        hx,hy=receta(nombre,n)['activo']
        # El extremo de escritura queda cubierto en el píxel de siempre.
        d.disco((hx+0.5)*32/n,(hy+0.5)*32/n,0.45)
    elif nombre=='color-picker':
        d.trazo([(7.1,24.7),(20.6,11.2)],5.2)
        d.trazo([(17.4,9.9),(23.0,15.5)],4.3)
        d.trazo([(22.2,9.1),(25.4,5.9)],6.3)
        hx,hy=receta(nombre,n)['activo']
        d.trazo([(7.1,24.7),((hx+0.5)*32/n,(hy+0.5)*32/n)],2.8)
    elif nombre=='wait':
        d.aro(16,16,9.7,4.6)
    else:
        direcciones={'top_side':-90,'bottom_side':90,'left_side':180,'right_side':0,
                     'top_left_corner':-135,'top_right_corner':-45,'bottom_left_corner':135,
                     'bottom_right_corner':45,'size_hor':0,'size_ver':90,'size_bdiag':-45,
                     'size_fdiag':45,'col-resize':0,'row-resize':90}
        a=math.radians(direcciones[nombre])
        def rotar(pts):
            return [(16+(x-16)*math.cos(a)-(y-16)*math.sin(a),
                     16+(x-16)*math.sin(a)+(y-16)*math.cos(a)) for x,y in pts]
        doble=nombre.startswith('size_') or nombre in ('col-resize','row-resize')
        if doble:
            pts=[(3.3,16),(10.6,8.8),(10.6,12.8),(21.4,12.8),(21.4,8.8),
                 (28.7,16),(21.4,23.2),(21.4,19.2),(10.6,19.2),(10.6,23.2)]
        else:
            pts=[(28.4,16),(19.8,8.4),(19.8,12.8),(5,12.8),(5,19.2),(19.8,19.2),(19.8,23.6)]
        d.poligono(rotar(pts),1.05)
        if nombre in ('col-resize','row-resize'):
            d.trazo(rotar([(16,7.6),(16,24.4)]),3.6)
    return centrar(d) if nombre not in ('pencil','color-picker') else d.m


def simbolo(nombre,n):
    """Insignias grandes: se comparten punta y tratamiento, no el arte antiguo."""
    d=Dibujo(n)
    if nombre=='copy':
        d.caja(19.5,16.2,28.4,26.4,1.9)
    elif nombre=='link':
        d.aro(19.2,19.6,3.6,2.8)
        d.aro(23.7,24.1,3.6,2.8)
        d.trazo([(19.5,19.9),(23.4,23.8)],2.4)
    elif nombre=='help':
        # Signo sólido con curvas amplias y punto separado.
        def curva(a,b,c,e):
            return [tuple((1-t)**3*a[j]+3*(1-t)**2*t*b[j]+3*(1-t)*t*t*c[j]+t**3*e[j] for j in (0,1))
                    for t in (i/24 for i in range(25))]
        pts=curva((19.4,18.3),(19.4,13.6),(27,13.6),(27,18.0))
        pts+=curva((27,18.0),(27,20.8),(23.4,20.8),(23.4,24.1))[1:]
        d.trazo(pts,3.1)
        d.disco(23.4,28.0,1.5)
    elif nombre=='context-menu':
        d.caja(17,17.3,29,28.8,2.6)
    return d.m


@lru_cache(maxsize=238)
def capa_estatica(nombre,n):
    from PIL import Image, ImageDraw
    forma=geometria(nombre,n)
    if nombre in ('text','vertical-text'):
        im=obsidiana_con_filo(forma,n,1.25 if nombre=='text' else 0,
                             0 if nombre=='text' else 1.25,
                             (12,8,16.3,24) if nombre=='text' else (8,12,24,16.3))
    elif nombre in ('crosshair','cell','fleur') or nombre.startswith('size_') or nombre.endswith('_side') or nombre.endswith('_corner') or nombre in ('col-resize','row-resize'):
        # Acento breve; los núcleos pequeños conservan obsidiana suficiente.
        limite=(12,0,17,13) if nombre in ('crosshair','fleur') else (0,0,15,13)
        im=obsidiana_con_filo(forma,n,0.9,0.2,limite)
    elif nombre in ('pointer','openhand','closedhand'):
        im=obsidiana_con_filo(forma,n,1.8,0.2,(0,0,14.8,32))
    elif nombre=='wait':
        im=obsidiana_con_filo(forma,n,lava=False)
    elif nombre=='not-allowed':
        im=obsidiana_con_filo(forma,n,1.7,0,(0,0,8,32))
    elif nombre in ('zoom-in','zoom-out'):
        im=obsidiana_con_filo(forma,n,1.7,0,(0,0,11.5,27))
    elif nombre=='color-picker':
        im=obsidiana_con_filo(forma,n,1.7,0,(0,10,18.5,32))
    else:
        im=obsidiana_con_filo(forma,n,2.4,-0.2)
    if nombre in ('help','copy','link','context-menu'):
        im.alpha_composite(obsidiana_con_filo(simbolo(nombre,n),n,lava=False))
        if nombre=='copy':
            d=Dibujo(n);d.caja(16.5,19.5,25.4,29.7,1.9)
            im.alpha_composite(obsidiana_con_filo(d.m,n,lava=False))
        elif nombre=='context-menu':
            d=ImageDraw.Draw(im);k=n*OPTICA[n][1]/32
            for y in (21,25.2):
                d.rounded_rectangle(tuple(v*k for v in (20,y-0.8,26,y+0.8)),radius=0.8*k,fill=BLANCO)
    if nombre in ('zoom-in','zoom-out'):
        hx,hy=receta(nombre,n)['activo'];ss=OPTICA[n][1];k=n*ss/32
        x,y=(hx+0.5)*ss,(hy+0.5)*ss
        d=ImageDraw.Draw(im)
        d.line((x-3.5*k,y,x+3.5*k,y),fill=BLANCO,width=round(2.2*k))
        if nombre=='zoom-in':d.line((x,y-3.5*k,x,y+3.5*k),fill=BLANCO,width=round(2.2*k))
    return im


def imagen_final(nombre,n,cuadro=0):
    from PIL import Image, ImageChops
    im=capa_estatica(nombre,n).copy()
    ss=OPTICA[n][1];k=n*ss/32
    if nombre in ('wait','progress'):
        d=Dibujo(n)
        if nombre=='wait':
            cx=cy=(n//2+0.5)*32/n;radio=9.7;ancho=4.6
        else:
            cx,cy,radio,ancho=23.0,23.2,4.8,3.2
            d.aro(cx,cy,radio,ancho)
            im.alpha_composite(obsidiana_con_filo(d.m,n,lava=False,borde=max(1.3,n/32*1.4)))
        d=Dibujo(n);d.aro(cx,cy,radio,ancho)
        tramo=Dibujo(n)
        inicio=-80+360*cuadro/CUADROS
        pts=[(cx+radio*math.cos(math.radians(inicio+112*j/64)),
              cy+radio*math.sin(math.radians(inicio+112*j/64))) for j in range(65)]
        tramo.trazo(pts,ancho)
        luz=degradado_lava(n).copy();luz.putalpha(ImageChops.multiply(tramo.m,d.m))
        im.alpha_composite(luz)
    return im.resize((n,n),Image.Resampling.LANCZOS)


TEMA=RAIZ/'files/system/usr/share/icons/Antu-Cursores'
VISTAS=RAIZ/'brand/previews/cursors'
INFORME=RAIZ/'brand/cursor-validation.json'
CUADROS=32
RETARDO=30
TIPO_IMAGEN=0xFFFD0002
FUENTE_BREEZE='https://raw.githubusercontent.com/KDE/breeze/master/cursors/Breeze/src/alias.list'
FUENTE_INVENTARIO='https://packages.debian.org/sid/all/breeze-cursor-theme/filelist'
# Inventario congelado e independiente del alias.tsv que se comprueba.
NOMBRES_BREEZE=frozenset(["00000000000000020006000e7e9ffc3f","00008160000006810000408080010102","03b6e0fcb3499374a867c041f52298f0","08e8e1c95fe2fc01f976f1e063a24ccd","1081e37283d90000800003c07f3ef6bf","3085a0e285430894940527032f8b26df","3ecb610c1bf2410f44200f48c40d3599","4498f0e0c1937ffe01fd06f973665830","5c6cd98b3f3ebcb1f9c7f1c204630408","6407b0e94181790501fd1e167b474872","640fb0e74195791501fd1ed57b41487f","9081237383d90e509aa00f00170e968f","9d800788f1b08800ae810202380a0822","a2a266d0498c3104214a47bd64ab0fc8","alias","all-scroll","arrow","b66166c04f8c3109214a4fbd64a50fc8","bottom_left_corner","bottom_right_corner","bottom_side","cell","center_ptr","circle","closedhand","col-resize","color-picker","context-menu","copy","cross","crossed_circle","crosshair","d9ce0ab605698f320427677b458ad60b","default","dnd-copy","dnd-move","dnd-no-drop","dnd-none","down-arrow","draft","e-resize","e29285e634086352946a0e7090d73106","ew-resize","fcf21c00b30f7e3f83fe0dfd12e71cff","fleur","forbidden","grab","grabbing","h_double_arrow","half-busy","hand1","hand2","help","ibeam","left-arrow","left_ptr","left_ptr_help","left_ptr_watch","left_side","link","move","n-resize","ne-resize","nesw-resize","no-drop","not-allowed","ns-resize","nw-resize","nwse-resize","openhand","pencil","pirate","plus","pointer","pointing_hand","progress","question_arrow","right-arrow","right_ptr","right_side","row-resize","s-resize","sb_h_double_arrow","sb_v_double_arrow","se-resize","size-bdiag","size-fdiag","size-hor","size-ver","size_all","size_bdiag","size_fdiag","size_hor","size_ver","split_h","split_v","sw-resize","tcross","text","top_left_arrow","top_left_corner","top_right_corner","top_side","up-arrow","v_double_arrow","vertical-text","w-resize","wait","watch","wayland-cursor","whats_this","x-cursor","xterm","zoom-in","zoom-out"])
REFERENCIA_ALIAS="00000000000000020006000e7e9ffc3f progress\n00008160000006810000408080010102 size_ver\n03b6e0fcb3499374a867c041f52298f0 circle\n08e8e1c95fe2fc01f976f1e063a24ccd progress\n3ecb610c1bf2410f44200f48c40d3599 progress\n5c6cd98b3f3ebcb1f9c7f1c204630408 help\n9d800788f1b08800ae810202380a0822 pointer\n640fb0e74195791501fd1ed57b41487f alias\n1081e37283d90000800003c07f3ef6bf copy\n3085a0e285430894940527032f8b26df alias\n4498f0e0c1937ffe01fd06f973665830 dnd-move\n6407b0e94181790501fd1e167b474872 copy\n9081237383d90e509aa00f00170e968f dnd-move\na2a266d0498c3104214a47bd64ab0fc8 alias\nb66166c04f8c3109214a4fbd64a50fc8 copy\nd9ce0ab605698f320427677b458ad60b help\ne29285e634086352946a0e7090d73106 pointer\nfcf21c00b30f7e3f83fe0dfd12e71cff dnd-move\nalias copy\nall-scroll fleur\narrow default\nbottom_left_corner size_bdiag\nbottom_right_corner size_fdiag\ncell crosshair\ncenter_ptr default\ncircle not-allowed\nclosedhand dnd-move\ncol-resize size_hor\ncolor-picker crosshair\ncontext-menu default\ncopy dnd-move\ncross crosshair\ncrossed_circle not-allowed\ndnd-copy copy\ndnd-none dnd-move\ndnd-no-drop not-allowed\ndraft pencil\ne-resize size_hor\new-resize size_hor\nforbidden no-drop\ngrab openhand\ngrabbing closedhand\nh_double_arrow size_hor\nhalf-busy progress\nhand1 pointer\nhand2 pointer\nhelp default\nibeam text\nleft_ptr default\nleft_ptr_help help\nleft_ptr_watch progress\nleft_side left-arrow\nlink alias\nmove dnd-move\nn-resize size_ver\nns-resize size_ver\nne-resize size_bdiag\nnesw-resize size_bdiag\nnw-resize size_fdiag\nnwse-resize size_fdiag\nno-drop not-allowed\nplus cell\npointing_hand pointer\nquestion_arrow help\nright_ptr default\nright_side right-arrow\nrow-resize size_ver\ns-resize size_ver\nse-resize size_fdiag\nsw-resize size_bdiag\nsb_h_double_arrow size_hor\nsb_v_double_arrow size_ver\nsize_all fleur\nsplit_h col-resize\nsplit_v row-resize\ntcross crosshair\ntop_left_arrow default\ntop_left_corner size_fdiag\ntop_right_corner size_bdiag\ntop_side up-arrow\nv_double_arrow size_ver\nvertical-text text\nw-resize size_hor\nwatch wait\nwhats_this help\nxterm text\ndnd-move default\ndown-arrow default\ncrosshair default\nfleur default\nleft-arrow default\nnot-allowed default\nopenhand default\npencil default\npirate default\npointer default\nprogress default\nright-arrow default\nsize-bdiag default\nsize-fdiag default\nsize-hor default\nsize-ver default\ntext default\nup-arrow default\nwait default\nx-cursor default\nwayland-cursor default\nzoom-in default\nzoom-out default"
ETIQUETAS=dict(zip(FORMAS,('Flecha','Enlace','Mano abierta','Mano cerrada','Texto','Texto vertical',
    'Precisión','Ayuda','Prohibido','Copiar','Enlace simbólico','Menú contextual','Celda','Mover',
    'Borde superior','Borde inferior','Borde izquierdo','Borde derecho','Esquina sup. izq.',
    'Esquina sup. der.','Esquina inf. izq.','Esquina inf. der.','Doble horizontal','Doble vertical',
    'Doble diagonal /','Doble diagonal \\','Columnas','Filas','Acercar','Alejar','Lápiz','Cuentagotas','Espera','Progreso')))


def alias_esperados():
    referencia=dict(linea.split() for linea in REFERENCIA_ALIAS.splitlines() if linea.strip())
    # Estados que tienen forma propia en Antu; se evita la cadena de alias de Breeze.
    referencia.update({'alias':'link','dnd-move':'closedhand','move':'fleur','all-scroll':'fleur',
        'down-arrow':'bottom_side','up-arrow':'top_side','left-arrow':'left_side','right-arrow':'right_side',
        'pirate':'not-allowed','x-cursor':'crosshair','wayland-cursor':'default',
        'size-bdiag':'size_bdiag','size-fdiag':'size_fdiag','size-hor':'size_hor','size-ver':'size_ver'})
    resultado={}
    for nombre in sorted(NOMBRES_BREEZE-set(FORMAS)):
        actual=nombre;vistos=set()
        while actual not in FORMAS:
            if actual in vistos or actual not in referencia:raise ValueError(f'Alias sin resolución: {nombre}')
            vistos.add(actual);actual=referencia[actual]
        resultado[nombre]=actual
    return resultado


def guardar_texto(ruta,texto):
    ruta.parent.mkdir(parents=True,exist_ok=True)
    ruta.write_text(texto,encoding='utf-8',newline='\n')


def metadatos():
    guardar_texto(TEMA/'index.theme','[Icon Theme]\nName=Antu Cursores\n'
        'Comment=Punta redonda, obsidiana sólida, contorno blanco y un filo de lava\n'
        'Inherits=breeze_cursors\nX-KDE-License=CC-BY-SA-4.0\n')
    guardar_texto(TEMA/'COPYING','Antu Cursores — arte original de Antu OS\n'
        'Copyright © 2026 Antu OS\nSPDX-License-Identifier: CC-BY-SA-4.0\n\n'
        'Este arte se distribuye bajo Creative Commons Atribución-CompartirIgual 4.0 Internacional.\n'
        'Se permite compartirlo y adaptarlo con atribución a Antu OS, indicando los cambios y\n'
        'distribuyendo las adaptaciones bajo la misma licencia.\n'
        'Licencia completa: https://creativecommons.org/licenses/by-sa/4.0/legalcode.es\n\n'
        'Solo se reutilizan los nombres compatibles de Breeze. No se incluye su arte.\n')
    guardar_texto(TEMA/'alias.tsv',''.join(f'{a}\t{o}\n' for a,o in alias_esperados().items()))


def escribir_xcursor(ruta,cuadros):
    # uint32 ARGB premultiplicado little-endian = bytes B,G,R,A.
    entradas=[];fragmentos=[];pos=16+12*len(cuadros)
    for n,im,activo,retardo in cuadros:
        pixeles=bytearray()
        rgba=im.tobytes()
        for r,g,b,a in zip(rgba[0::4],rgba[1::4],rgba[2::4],rgba[3::4]):pixeles.extend(((b*a+127)//255,(g*a+127)//255,(r*a+127)//255,a))
        chunk=struct.pack('<9I',36,TIPO_IMAGEN,n,1,n,n,*activo,retardo)+pixeles
        entradas.append(struct.pack('<3I',TIPO_IMAGEN,n,pos));fragmentos.append(chunk);pos+=len(chunk)
    ruta.write_bytes(struct.pack('<4s3I',b'Xcur',16,0x10000,len(cuadros))+b''.join(entradas)+b''.join(fragmentos))


def leer_xcursor(datos):
    # No comparte el escritor ni usa Pillow: cada límite se verifica antes de leer.
    def exigir(condicion,mensaje):
        if not condicion:raise ValueError(mensaje)
    exigir(len(datos)>=16,'Cabecera truncada')
    firma,cabecera,version,total=struct.unpack_from('<4s3I',datos)
    exigir(firma==b'Xcur' and cabecera==16 and version==0x10000,'Cabecera Xcursor inválida')
    exigir(0<total<=1000 and 16+total*12<=len(datos),'Tabla de contenido inválida')
    esperado=16+total*12;resultado=[]
    for i in range(total):
        tipo,nominal,pos=struct.unpack_from('<3I',datos,16+12*i)
        exigir(tipo==TIPO_IMAGEN,'Tipo de fragmento desconocido')
        exigir(pos==esperado and pos+36<=len(datos),'Offset no contiguo, solapado o truncado')
        h,t,s,v,ancho,alto,hx,hy,retardo=struct.unpack_from('<9I',datos,pos)
        exigir((h,t,s,v)==(36,tipo,nominal,1),'Cabecera de imagen inconsistente')
        exigir(0<ancho<=1024 and 0<alto<=1024,'Dimensión fuera de límites')
        exigir(ancho==alto==nominal,'Tamaño nominal no coincide con el lienzo')
        exigir(hx<ancho and hy<alto,'Punto activo fuera de imagen')
        fin=pos+h+ancho*alto*4;exigir(fin<=len(datos),'Píxeles truncados')
        pixeles=datos[pos+h:fin];alfa=pixeles[3::4]
        exigir(max(alfa)>0,'Imagen vacía')
        exigir(min(alfa)==0,'Falta margen transparente')
        exigir(all(b<=a and g<=a and r<=a for b,g,r,a in zip(pixeles[0::4],pixeles[1::4],pixeles[2::4],alfa)),
               'ARGB no premultiplicado: canal de color mayor que alfa')
        resultado.append(dict(tamano=nominal,ancho=ancho,alto=alto,activo=(hx,hy),retardo=retardo,pixeles=pixeles))
        esperado=fin
    exigir(esperado==len(datos),'Bytes finales sin declarar')
    return resultado


def a_imagen(cuadro):
    from PIL import Image
    salida=bytearray()
    for b,g,r,a in zip(cuadro['pixeles'][0::4],cuadro['pixeles'][1::4],cuadro['pixeles'][2::4],cuadro['pixeles'][3::4]):
        salida.extend((min(255,(r*255+a//2)//a) if a else 0,min(255,(g*255+a//2)//a) if a else 0,
                       min(255,(b*255+a//2)//a) if a else 0,a))
    return Image.frombytes('RGBA',(cuadro['ancho'],cuadro['alto']),bytes(salida))



# Luminancia relativa sRGB, sin Pillow y calculada sobre los bytes Xcursor reales.
LUMINANCIA = tuple(v/255/12.92 if v/255<=0.04045 else ((v/255+0.055)/1.055)**2.4 for v in range(256))
FONDOS_CONTRASTE = {'negro':0, 'gris128':128, 'blanco':255}


def contar_contraste(cuadro,fondo):
    """Compone ARGB premultiplicado sobre el fondo antes de medir 3:1."""
    luminancia_fondo=LUMINANCIA[fondo]
    cuenta=0
    p=cuadro['pixeles']
    for b,g,r,a in zip(p[0::4],p[1::4],p[2::4],p[3::4]):
        resto=(fondo*(255-a)+127)//255
        rojo,verde,azul=(min(255,v+resto) for v in (r,g,b))
        lum=0.2126*LUMINANCIA[rojo]+0.7152*LUMINANCIA[verde]+0.0722*LUMINANCIA[azul]
        razon=(max(lum,luminancia_fondo)+0.05)/(min(lum,luminancia_fondo)+0.05)
        cuenta+=razon>=3.0
    return cuenta


def validar():
    errores=[];archivos=[];resumen={};contrastes={}
    def comprobar(cond,mensaje):
        if not cond:errores.append(mensaje)
    try:
        cp=configparser.ConfigParser(interpolation=None);cp.read(TEMA/'index.theme',encoding='utf-8')
        comprobar(cp['Icon Theme']['Name']=='Antu Cursores','Nombre incorrecto')
        comprobar(cp['Icon Theme']['Inherits']=='breeze_cursors','Herencia incorrecta')
        comprobar('lava' in cp['Icon Theme']['Comment'],'Falta comentario en español')
        comprobar('CC-BY-SA-4.0' in (TEMA/'COPYING').read_text(encoding='utf-8'),'Licencia ausente')
    except Exception as e:errores.append(f'Metadatos: {e}')
    for nombre in FORMAS:
        ruta=TEMA/'cursors'/nombre
        try:
            comprobar(not ruta.is_symlink(),f'{nombre}: enlace simbólico no autorizado')
            datos=ruta.read_bytes();cuadros=leer_xcursor(datos)
            grupos=collections.defaultdict(list)
            for c in cuadros:grupos[c['tamano']].append(c)
            comprobar(set(grupos)==set(TAMANOS),f'{nombre}: tamaños incorrectos {sorted(grupos)}')
            cantidad=CUADROS if nombre in ('wait','progress') else 1
            for n,grupo in grupos.items():
                comprobar(len(grupo)==cantidad,f'{nombre}/{n}: número de cuadros incorrecto')
                comprobar(all(c['retardo']==(RETARDO if cantidad>1 else 0) for c in grupo),f'{nombre}/{n}: retardo incorrecto')
                comprobar(all(c['activo']==receta(nombre,n)['activo'] for c in grupo),f'{nombre}/{n}: punto activo no coincide con su geometría')
                if n in MINIMO_CONTRASTE:
                    medidas={bg:[contar_contraste(c,valor) for c in grupo] for bg,valor in FONDOS_CONTRASTE.items()}
                    contrastes[f'{nombre}/{n}']={
                        'minimo_exigido':MINIMO_CONTRASTE[n],
                        'pixeles_3_a_1':{bg:min(v) for bg,v in medidas.items()},
                        'por_cuadro':medidas}
                    for bg,cuentas in medidas.items():
                        comprobar(min(cuentas)>=MINIMO_CONTRASTE[n],
                            f'{nombre}/{n}: contraste sobre {bg}: {min(cuentas)} < {MINIMO_CONTRASTE[n]} píxeles a 3:1')
                if nombre in ('default','pointer','pencil','color-picker'):
                    hx,hy=grupo[0]['activo'];comprobar(grupo[0]['pixeles'][(hy*n+hx)*4+3]>32,f'{nombre}/{n}: punta activa transparente')
                if cantidad>1:
                    comprobar(len({c['pixeles'] for c in grupo})==cantidad,f'{nombre}/{n}: cuadros duplicados')
                    # Detecta un salto de cierre mucho mayor que el avance normal.
                    cambios=[sum(abs(a-b) for a,b in zip(grupo[i]['pixeles'],grupo[(i+1)%cantidad]['pixeles'])) for i in range(cantidad)]
                    comprobar(max(cambios)<min(cambios)*3,f'{nombre}/{n}: salto en el bucle')
                resumen[f'{nombre}/{n}']={'cuadros':len(grupo),'retardos_ms':sorted({c['retardo'] for c in grupo}),
                    'activo':grupo[0]['activo'],'ancho':grupo[0]['ancho'],'alto':grupo[0]['alto']}
            archivos.append({'nombre':nombre,'bytes':len(datos),'fragmentos':len(cuadros),'sha256':hashlib.sha256(datos).hexdigest()})
        except Exception as e:errores.append(f'{nombre}: {e}')
    try:
        presentes={p.name for p in (TEMA/'cursors').iterdir()}
        comprobar(presentes==set(FORMAS),f'Archivos de cursor inesperados o ausentes: {sorted(presentes^set(FORMAS))}')
        aliases={}
        for numero,linea in enumerate((TEMA/'alias.tsv').read_text(encoding='utf-8').splitlines(),1):
            campos=linea.split('\t')
            if len(campos)!=2:errores.append(f'alias.tsv:{numero}: se requieren dos columnas');continue
            a,o=campos
            comprobar(a not in aliases,f'Alias duplicado: {a}')
            comprobar(a not in presentes,f'Alias colisiona con una forma: {a}')
            comprobar(a and '/' not in a and '\\' not in a and a not in ('.','..'),f'Nombre de alias inválido: {a}')
            comprobar(o in presentes and (TEMA/'cursors'/o).is_file(),f'{a}: original inexistente {o}')
            aliases[a]=o
        comprobar(aliases==alias_esperados(),'El mapa de alias difiere del contrato semántico')
        faltantes=sorted(NOMBRES_BREEZE-(presentes|set(aliases)))
        comprobar(not faltantes,f'Nombres de Breeze sin cubrir: {faltantes}')
        comprobar(len(NOMBRES_BREEZE)==115,'Inventario de Breeze alterado')
        for p in (TEMA/'index.theme',TEMA/'COPYING',TEMA/'alias.tsv'):
            comprobar(b'\r' not in p.read_bytes(),f'{p.name}: saltos de línea distintos de LF')
    except Exception as e:
        aliases={};faltantes=sorted(NOMBRES_BREEZE);errores.append(f'Inventario: {e}')
    try:
        corrupciones=pruebas_lector()
        comprobar(corrupciones==6,'Autocomprobación incompleta del lector')
        comprobar(contar_contraste({'pixeles':bytes((0,0,0,0))*576},128)==0,
                   'Medición de contraste: fondo transparente contado como visible')
        comprobar(contar_contraste({'pixeles':bytes((128,128,128,255))*576},128)==0,
                   'Medición de contraste: gris sobre sí mismo contado como visible')
    except Exception as e:
        corrupciones=0;errores.append(f'Autocomprobación: {e}')
    resultado={'tema':'Antu Cursores','correcto':not errores,'errores':errores,'formas':len(FORMAS),
        'archivos_leidos':len(archivos),'alias':len(aliases),'nombres_breeze':len(NOMBRES_BREEZE),
        'nombres_breeze_cubiertos':115-len(faltantes),'nombres_faltantes':faltantes,
        'tamanos':TAMANOS,'animacion':{'cuadros_por_tamano':CUADROS,'retardo_ms':RETARDO,'bucle_ms':CUADROS*RETARDO},
        'fragmentos_totales':sum(a['fragmentos'] for a in archivos),
        'corrupciones_rechazadas':corrupciones,'contraste':{'umbral_razon':3.0,
            'minimos_pixeles_por_tamano':MINIMO_CONTRASTE,
            'metodo':'Composición sRGB de ARGB premultiplicado sobre negro, gris 128 y blanco; luminancia relativa WCAG; se exige el mínimo en todos los cuadros.',
            'formas':contrastes},
        'comprobaciones':['Contraste medido de cada forma a 24/32 en tres fondos y todos los cuadros','Seis corrupciones rechazadas por el lector','Cabecera y TOC little-endian','Offsets, límites y ausencia de bytes residuales',
            'Siete tamaños exactos','Cuadros y retardos','Hotspots según receta óptica',
            'Imágenes no vacías','Canales de color menores o iguales a alfa',
            'Alias directos, sin enlaces, duplicados ni ciclos','Cobertura independiente de 115 nombres',
            'Cuadros únicos y continuidad del bucle'],
        'fuentes_nombres':{'alias':FUENTE_BREEZE,'inventario':FUENTE_INVENTARIO,'consulta':'2026-11-02',
            'sha256_nombres':hashlib.sha256(('\n'.join(sorted(NOMBRES_BREEZE))+'\n').encode()).hexdigest()},
        'limites':['No ejecutado en una sesión KDE/Wayland/X11 real.','No probado dentro de un juego real ni con alias materializados en Linux.'],
        'imagenes':resumen,'archivos':archivos}
    guardar_texto(INFORME,json.dumps(resultado,ensure_ascii=False,indent=2)+'\n')
    if errores:
        for error in errores:print('ERROR: '+error)
        print(f'VALIDACIÓN FALLIDA: {len(errores)} errores. Informe: brand/cursor-validation.json')
        return False
    print(f'Contraste: {len(contrastes)} formas/tamaño × 3 fondos; mínimos 40 px a 24 y 72 px a 32, todos a 3:1. Seis corrupciones rechazadas.')
    print(f'VALIDACIÓN CORRECTA: {len(archivos)} Xcursor, {len(aliases)} alias; 115/115 nombres Breeze; '
          f'7 tamaños; {resultado["fragmentos_totales"]} fragmentos; wait/progress {CUADROS} cuadros × {RETARDO} ms.')
    return True


def pruebas_lector():
    # Autocomprobaciones adversas en memoria: no alteran los recursos entregados.
    datos=(TEMA/'cursors/default').read_bytes();primer_offset=struct.unpack_from('<I',datos,24)[0]
    casos={'firma':(0,b'NOPE'),'offset':(24,struct.pack('<I',16)),
        'hotspot':(primer_offset+24,struct.pack('<I',999)),
        'premultiplicado':(primer_offset+36,bytes((255,0,0,0)))}
    for nombre,(pos,valor) in casos.items():
        corrupto=bytearray(datos);corrupto[pos:pos+len(valor)]=valor
        try:leer_xcursor(corrupto)
        except ValueError:continue
        raise ValueError(f'El lector aceptó corrupción: {nombre}')
    for nombre,corrupto in [('truncado',datos[:-1]),('residuo',datos+b'X')]:
        try:leer_xcursor(corrupto)
        except ValueError:continue
        raise ValueError(f'El lector aceptó corrupción: {nombre}')
    return 6


def vistas():
    from PIL import Image,ImageDraw,ImageFont,ImageOps
    VISTAS.mkdir(parents=True,exist_ok=True)
    try:
        fuente=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',14)
        pequena=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',11)
        titulo=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',26)
    except OSError:fuente=pequena=titulo=ImageFont.load_default()
    def letra(draw,xy,txt,claro=True,font=None):draw.text(xy,txt,font=font or fuente,fill='#e5e7eb' if claro else '#222630')
    catalogo={nom:leer_xcursor((TEMA/'cursors'/nom).read_bytes()) for nom in FORMAS}
    def cursor(nom,n,i=0):return a_imagen([c for c in catalogo[nom] if c['tamano']==n][i])
    def fondo(nombre,tam):
        if nombre in ('negro','blanco','gris'):return Image.new('RGB',tam,{'negro':'#000000','blanco':'#ffffff','gris':'#808080'}[nombre])
        if nombre=='juego':
            # Prueba deliberadamente sintética: HUD, alta frecuencia, luces y sombras.
            im=Image.new('RGB',tam,'#11202d');d=ImageDraw.Draw(im)
            w,h=tam
            for y in range(h):
                v=y/h;d.line((0,y,w,y),fill=(int(12+38*v),int(23+40*v),int(39+25*v)))
            for i in range(28):
                x=(i*113)%w;y=(i*73)%h
                d.polygon([(x,y),(x+90,y-75),(x+150,h),(x-30,h)],fill=('#273d3c' if i%2 else '#142a31'))
                d.line((x,y,x+90,y-75),fill='#83a790',width=2)
            d.line((w//2-25,h//2,w//2+25,h//2),fill='#d5e8de',width=1)
            d.line((w//2,h//2-25,w//2,h//2+25),fill='#d5e8de',width=1)
            d.rectangle((24,h-44,184,h-28),fill='#f2ab42')
            return im
        archivo=RAIZ/f'files/system/usr/share/wallpapers/{nombre}/contents/images/3840x2160.jpg'
        with Image.open(archivo) as im:return ImageOps.fit(im.convert('RGB'),tam,method=Image.Resampling.LANCZOS)
    hojas=[]
    for bg in ('negro','blanco','gris','Paranal'):
        hoja=fondo(bg,(1320,1180));d=ImageDraw.Draw(hoja);claro=bg!='blanco'
        letra(d,(24,16),'Antu Cursores / '+bg,claro,titulo)
        letra(d,(24,52),'34 formas · 24 / 32 / 48 / 96 px · tamaño real · sin reescalar la hoja',claro)
        for j,nom in enumerate(FORMAS):
            x=24+(j%5)*260;y=100+(j//5)*152
            letra(d,(x,y),ETIQUETAS[nom],claro)
            for n,dx in ((24,0),(32,38),(48,86),(96,150)):
                im=cursor(nom,n);hoja.paste(im,(x+dx,y+32),im)
                letra(d,(x+dx,y+132),str(n),claro,pequena)
        hoja.save(VISTAS/f'formas-{bg.lower()}.png');hojas.append(hoja)
    mosaico=Image.new('RGB',(2640,2360))
    for i,hoja in enumerate(hojas):mosaico.paste(hoja,((i%2)*1320,(i//2)*1180))
    mosaico.save(VISTAS/'hoja-todas.png')
    # Revisión concentrada: las 34 formas pequeñas sobre cuatro fondos.
    pequeno=Image.new('RGB',(1360,1610),'#111318');d=ImageDraw.Draw(pequeno)
    letra(d,(20,16),'Lectura diaria / 24 y 32 px',True,titulo)
    for col,bg in enumerate(('negro','blanco','gris','Paranal')):
        panel=fondo(bg,(330,1520));p=ImageDraw.Draw(panel);claro=bg!='blanco'
        for j,nom in enumerate(FORMAS):
            yy=18+j*44
            letra(p,(12,yy+7),ETIQUETAS[nom],claro,pequena)
            for n,xx in ((24,222),(32,272)):
                im=cursor(nom,n);panel.paste(im,(xx,yy),im)
        pequeno.paste(panel,(col*340,75));letra(d,(col*340+12,55),bg,True,pequena)
    pequeno.save(VISTAS/'lectura-24-32.png')
    # Ampliación NEAREST exacta; el borde cian señala la celda del hotspot.
    zoom=Image.new('RGB',(1060,630),'#181b21');d=ImageDraw.Draw(zoom)
    letra(d,(22,15),'Flecha / píxel exacto ×8',True,titulo)
    letra(d,(22,51),'Cian: celda del punto activo. Arriba 24 px; abajo 32 px. Sin suavizado al ampliar.',True)
    for row,n in enumerate((24,32)):
        for col,bg in enumerate(('negro','blanco','gris','Paranal')):
            xx=20+col*260;yy=100+row*240
            base=fondo(bg,(n,n));im=cursor('default',n);base.paste(im,(0,0),im)
            base=base.resize((n*8,n*8),Image.Resampling.NEAREST);zoom.paste(base,(xx,yy))
            hx,hy=receta('default',n)['activo'];d.rectangle((xx+hx*8,yy+hy*8,xx+(hx+1)*8-1,yy+(hy+1)*8-1),outline='#35dce6',width=1)
            letra(d,(xx,yy-22),f'{bg} · {n} px · activo ({hx}, {hy})',True,pequena)
    zoom.save(VISTAS/'flecha-pixeles.png')
    # El GIF usa todos los cuadros del Xcursor, incluida la transición 31 -> 0.
    gifs=[]
    for i in range(CUADROS):
        cuadro=Image.new('RGB',(960,600),'#171a20');draw=ImageDraw.Draw(cuadro)
        letra(draw,(20,12),'Espera y progreso / 32 cuadros · 30 ms · bucle de 960 ms',True,titulo)
        for row,bg in enumerate(('negro','blanco')):
            panel=fondo(bg,(920,230));p=ImageDraw.Draw(panel)
            for col,n in enumerate((24,32,48,96)):
                x=18+col*226
                for nom,y in (('wait',10),('progress',125)):
                    im=cursor(nom,n,i);panel.paste(im,(x,y),im)
                letra(p,(x+110,35),str(n)+' px',bg!='blanco')
            cuadro.paste(panel,(20,70+row*245))
        gifs.append(cuadro)
    # Paleta compartida: evita parpadeo de cuantización entre cuadros.
    paleta=Image.new('RGB',(960,600*CUADROS))
    for i,im in enumerate(gifs):paleta.paste(im,(0,i*600))
    paleta=paleta.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
    gifcuadros=[im.quantize(palette=paleta,dither=Image.Dither.NONE) for im in gifs]
    gifcuadros[0].save(VISTAS/'espera-progreso.gif',save_all=True,append_images=gifcuadros[1:],duration=30,loop=0,disposal=2,optimize=False)
    contacto=Image.new('RGB',(1024,320),'#101317');d=ImageDraw.Draw(contacto)
    for i in range(CUADROS):
        xx=(i%16)*64+8;yy=(i//16)*148+20
        for nom,dy in (('wait',0),('progress',60)):
            im=cursor(nom,48,i);contacto.paste(im,(xx,yy+dy),im)
        letra(d,(xx,yy+112),str(i),True,pequena)
    contacto.save(VISTAS/'animacion-contacto.png')
    # Vistas de contraste sin oscurecer los fondos aprobados.
    contraste=Image.new('RGB',(1320,1040),'#16191f');d=ImageDraw.Draw(contraste)
    letra(d,(22,12),'Fondos aprobados y escena de juego sintética / 24 y 32 px',True,titulo)
    for j,bg in enumerate(('Paranal','Antu','Salar','juego')):
        panel=fondo(bg,(640,450));p=ImageDraw.Draw(panel)
        p.rectangle((0,0,640,37),fill='#11151b');letra(p,(14,8),bg if bg!='juego' else 'Juego: escenario sintético, no captura real')
        for i,nom in enumerate(('default','pointer','text','crosshair','wait','progress','not-allowed','pencil','color-picker','cell','fleur','openhand')):
            xx=25+(i%6)*103;yy=85+(i//6)*180
            for n,dx in ((24,0),(32,40)):
                im=cursor(nom,n);panel.paste(im,(xx+dx,yy),im)
        contraste.paste(panel,(20+(j%2)*660,70+(j//2)*480))
    contraste.save(VISTAS/'contraste-fondos.png')
    comparacion(catalogo,fuente,pequena,titulo)




def comparacion(catalogo,fuente,pequena,titulo):
    """Referencia ejecutada desde la fuente aprobada, que se conserva intacta."""
    from PIL import Image,ImageDraw
    codigo=(VISTAS/'maqueta-moderna.py').read_text(encoding='utf-8')
    funciones='from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont\n'+codigo[codigo.index('S = 16'):codigo.index('OPCIONES =')]
    referencia={}
    exec(compile(funciones,'maqueta-moderna.py','exec'),referencia)
    originales=[referencia['obsidiana_con_filo'](referencia[nom](),dx,dy)
                for nom,dx,dy in (('punta',2.4,-0.2),('mano',2.3,0.2),('barra',1.5,0))]
    hoja=Image.new('RGB',(1260,930),'#15151a');d=ImageDraw.Draw(hoja)
    d.text((24,16),'Punta aprobada / familia entregada',font=titulo,fill='white')
    d.text((24,55),'Referencia: funciones originales de maqueta-moderna.py. Entrega: bytes de los Xcursor finales.',font=fuente,fill='#ccccd2')
    for col,(nom,titulo_forma) in enumerate((('default','Punta'),('pointer','Mano de enlace'),('text','Texto'))):
        x=22+col*416
        d.text((x,94),titulo_forma,font=titulo,fill='white')
        for row,n in enumerate((96,24,32)):
            yy=145+row*240
            panel=Image.new('RGB',(396,205),'#808080')
            pd=ImageDraw.Draw(panel)
            pd.text((16,10),f'{n} px'+(' / ×4' if n<96 else ' / tamaño real'),font=fuente,fill='#08080b')
            for i,im in enumerate((originales[col].resize((n,n),Image.Resampling.LANCZOS),
                                  a_imagen(next(c for c in catalogo[nom] if c['tamano']==n)))):
                ancho=n if n==96 else n*4
                base=Image.new('RGB',(n,n),'#808080');base.paste(im,(0,0),im)
                if n<96:base=base.resize((ancho,ancho),Image.Resampling.NEAREST)
                panel.paste(base,(24+i*190,43))
                pd.text((24+i*190,178),'Maqueta' if i==0 else 'Antu entregado',font=pequena,fill='#08080b')
            hoja.paste(panel,(x,yy))
    d.text((24,893),'La flecha mantiene los vértices aprobados; el blanco y el cuerpo se refuerzan en las formas pequeñas.',font=fuente,fill='#ccccd2')
    hoja.save(VISTAS/'comparacion-maqueta.png')


def generar():
    (TEMA/'cursors').mkdir(parents=True,exist_ok=True)
    metadatos()
    for nom in FORMAS:
        cuadros=[]
        for n in TAMANOS:
            for i in range(CUADROS if nom in ('wait','progress') else 1):
                im=imagen_final(nom,n,i)
                if i==0:
                    destino=MAESTROS/'2d'/nom/f'{n}.png'
                    destino.parent.mkdir(parents=True,exist_ok=True)
                    im.save(destino)
                cuadros.append((n,im,receta(nom,n)['activo'],RETARDO if nom in ('wait','progress') else 0))
        escribir_xcursor(TEMA/'cursors'/nom,cuadros)
        print(f'ANTU 2D {nom}: siete tamaños',flush=True)
    guardar_texto(MAESTROS/'recetas-opticas.json',json.dumps({str(n):{
        'contorno_blanco_px':OPTICA[n][0],'supermuestreo':OPTICA[n][1],
        'cuerpo':'#111115','contorno':'#FFFFFF',
        'sombra':{'desplazamiento_y':1.3*n/32,'desenfoque':2.1*n/32,'opacidad':0.5},
        'ajuste':'Geometría propia; encaje del extremo y centros en el píxel activo.'}
        for n in TAMANOS},ensure_ascii=False,indent=2)+'\n')
    vistas()
    return validar()


def principal():
    p=argparse.ArgumentParser(description='Dibujar Antu Cursores en 2D con Pillow, empaquetar Xcursor y validar. --validar solo necesita la biblioteca estándar.')
    p.add_argument('--validar',action='store_true',help='Leer el tema sin regenerarlo y escribir el informe; falla si incumple el contrato o el contraste')
    a=p.parse_args()
    try:
        correcto=validar() if a.validar else generar()
    except Exception as e:
        print(f'ERROR: {e}')
        raise SystemExit(1)
    raise SystemExit(0 if correcto else 1)


if __name__=='__main__':
    principal()
