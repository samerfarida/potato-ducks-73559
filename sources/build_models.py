"""Editable, millimetre-scale Potato Ducks printable relief models.
Run: python build_models.py. Output goes to the repository layout, or to the directory set in POTATO_DUCKS_OUTPUT.
Dependencies: see requirements.txt beside this script.
"""
from pathlib import Path
import json, math, os, zipfile, struct
import numpy as np
import trimesh
from shapely.geometry import Point, Polygon, LineString, box
from shapely.affinity import scale, translate, rotate
from shapely.ops import unary_union
from shapely import set_precision
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
import xml.etree.ElementTree as ET
ROOT=Path(os.environ.get("POTATO_DUCKS_OUTPUT", Path(__file__).resolve().parent.parent))
for folder in ("models/3mf","models/stl","print/coin","docs","validation","sources"):
    (ROOT/folder).mkdir(parents=True,exist_ok=True)
COLORS={'navy':'#172840','gold':'#E9AE35','brown':'#A8652D','yellow':'#FFCE21','orange':'#F47721','black':'#161719'}
FONT=FontProperties(family='DejaVu Sans',weight='bold')
COIN_RADIUS=30.0
BASE=1.6
FACE=0.8

def ellipse(x,y,rx,ry):return translate(scale(Point(0,0).buffer(1,quad_segs=48),rx,ry),x,y)
def poly(coords):return Polygon(coords).buffer(0)
def stroke(coords,w):return LineString(coords).buffer(w/2,cap_style='round',join_style='round')
def text(s,size,x,y):
    paths=TextPath((0,0),s,size=size,prop=FONT).to_polygons()
    g=Polygon()
    for p in paths:g=g.symmetric_difference(Polygon(p))
    b=g.bounds
    return translate(g,x-(b[0]+b[2])/2,y-(b[1]+b[3])/2)
def arc(s,r,size):
    widths=[TextPath((0,0),c,size=size,prop=FONT).get_extents().width if c!=' ' else size*.38 for c in s]
    advance=[w+size*.15 for w in widths]; total=sum(advance); cur=-total/2; out=[]
    for c,w,a in zip(s,widths,advance):
        angle=(cur+a/2)/r
        if c!=' ':out.append(translate(rotate(text(c,size,0,0),-math.degrees(angle),origin=(0,0)),r*math.sin(angle),r*math.cos(angle)))
        cur+=a
    return unary_union(out)

def mascot():
    layers=[]
    def paint(g,c,outline=True):
        if outline:layers.append(('black',g.buffer(.52)))
        layers.append((c,g))
    # Potato body, lifted flexing arms, and broad webbed feet.
    body=unary_union([ellipse(0,-5.5,7.8,10.2),ellipse(4,-9,4.4,6)])
    for side in [-1,1]:
        def flip(g):return scale(g,xfact=side,yfact=1,origin=(0,0))
        arm=unary_union([ellipse(9,-1,4.7,3.6),stroke([(9,-2),(15,-1),(15.4,5.8),(13,8)],4.5),ellipse(13,8,3.6,2.8)])
        paint(flip(arm),'yellow')
        # Finger separations and biceps definition.
        for line in [[(11.4,9.5),(12.4,7.8)],[(13,10),(14,8.4)],[(7.3,-.3),(10,-1.3),(12,-.8)]]:
            layers.append(('black',flip(stroke(line,.6))))
    paint(body,'brown')
    for x,y in [(-3,-4),(3,-2),(-4,-10),(4,-11),(0,-7)]:layers.append(('black',ellipse(x,y,.55,.45)))
    for side in [-1,1]:
        foot=poly([(side*3,-14),(side*4,-17),(side*8,-18),(side*6,-19.3),(side*1.5,-18.8),(side*2,-17)])
        paint(foot,'orange')
    head=unary_union([ellipse(0,8.3,7,7.2),ellipse(-3.2,5,4.3,3.6)])
    paint(head,'yellow')
    # Angular, determined eyes and brows, inspired by shirt.
    paint(poly([(-5,10),(-1.9,8.8),(-2.3,6.2),(-4.8,6.9)]),'gold')
    paint(poly([(1.1,8.8),(4.8,10.4),(4.3,7),(1.6,6.1)]),'gold')
    layers.append(('black',ellipse(-2.8,7.7,.7,1.3)))
    layers.append(('black',ellipse(2.7,8,.8,1.4)))
    layers.append(('black',stroke([(-5.3,10.8),(-2.1,9.2)],.95)))
    layers.append(('black',stroke([(1,9.3),(4.9,11)],.95)))
    bill=poly([(-3.3,6),(-.7,5),(3,4.7),(3.6,3.4),(1.6,2.1),(-3.3,2),(-8,3),(-9.6,4.2),(-8.8,5.2),(-5.3,5.1)])
    def compact_bill(g):return scale(g,xfact=.68,yfact=.82,origin=(0,4.4))
    paint(compact_bill(bill).buffer(.35),'orange')
    layers.append(('black',stroke([(-5.7,4.07),(-2.72,3.66),(.068,3.58),(1.63,4.07)],.55)))
    layers.append(('black',ellipse(-2.1,4.97,.44,.33)))
    return layers

def regions(layers,clip):
    clip=set_precision(clip,0.001); reg={c:Polygon() for c in COLORS}; used=Polygon()
    for c,g in reversed(layers):
        g=set_precision(g.buffer(0),0.001).simplify(0.005,preserve_topology=True).intersection(clip).difference(used)
        reg[c]=reg[c].union(g)
        used=used.union(g)
    reg['navy']=reg['navy'].union(clip.difference(used))
    return {c:g.buffer(0) for c,g in reg.items() if not g.is_empty}
def extrude(g,z,h):
    parts=[]
    for p in ([g] if g.geom_type=='Polygon' else list(g.geoms)):
        if p.geom_type!='Polygon' or p.area<0.002:continue
        m=trimesh.creation.extrude_polygon(p,h,engine='earcut');m.apply_translation([0,0,z]);parts.append(m)
    return trimesh.util.concatenate(parts)
def make_meshes(reg,clip,base=BASE,face=FACE):
    clip=set_precision(clip,0.001)
    meshes={c:extrude(g,base,face) for c,g in reg.items()}
    meshes['navy']=trimesh.boolean.union([extrude(clip,0,base),meshes['navy']],engine='manifold')
    return meshes

def draw(ax,reg,title):
    for c,g in reg.items():
        for p in ([g] if g.geom_type=='Polygon' else g.geoms):
            if p.geom_type!='Polygon':continue
            verts=[];codes=[]
            from shapely.geometry.polygon import orient
            p=orient(p,sign=1)
            for ring in [p.exterior,*p.interiors]:
                xy=list(ring.coords);verts.extend(xy);codes.extend([MPath.MOVETO]+[MPath.LINETO]*(len(xy)-2)+[MPath.CLOSEPOLY])
            ax.add_patch(PathPatch(MPath(verts,codes),facecolor=COLORS[c],edgecolor='none'))
    ax.autoscale_view();ax.set_aspect('equal');ax.axis('off');ax.set_title(title,color='#172840',fontsize=13,pad=12)

NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
def write3mf(path,assemblies,four=False):
    ET.register_namespace('',NS)
    def sub(p,n,**a):return ET.SubElement(p,'{'+NS+'}'+n,{k:str(v) for k,v in a.items()})
    model=ET.Element('{'+NS+'}model',{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    sub(model,'metadata',name='Title').text='Potato Ducks FIRST LEGO Team 73559'
    res=sub(model,'resources'); mats=sub(res,'basematerials',id=1)
    names=['navy','brown','yellow','orange'] if four else list(COLORS)
    for c in names:sub(mats,'base',name=c,displaycolor=COLORS[{'gold':'yellow','black':'navy'}.get(c,c) if four else c]+'FF')
    oid=2;build_ids=[]; config=ET.Element('config')
    for name,meshes,offset in assemblies:
        ids=[]
        for c,m in meshes.items():
            obj=sub(res,'object',id=oid,type='model',name=name+'_'+c,pid=1,pindex=names.index({'gold':'yellow','black':'navy'}.get(c,c) if four else c));ids.append(oid);oid+=1
            mesh=sub(obj,'mesh');v=sub(mesh,'vertices');t=sub(mesh,'triangles')
            for x,y,z in m.vertices:sub(v,'vertex',x=f'{x:.6f}',y=f'{y:.6f}',z=f'{z:.6f}')
            for a,b,cidx in m.faces:sub(t,'triangle',v1=a,v2=b,v3=cidx)
        obj=sub(res,'object',id=oid,type='model',name=name);comp=sub(obj,'components')
        cfg=ET.SubElement(config,'object',id=str(oid))
        ET.SubElement(cfg,'metadata',key='name',value=name)
        for child,color in zip(ids,meshes):
            part=ET.SubElement(cfg,'part',id=str(child),subtype='normal_part')
            ET.SubElement(part,'metadata',key='name',value=name+'_'+color)
            index=names.index({'gold':'yellow','black':'navy'}.get(color,color) if four else color)+1
            ET.SubElement(part,'metadata',key='extruder',value=str(index))
        for i in ids:sub(comp,'component',objectid=i)
        build_ids.append((oid,offset));oid+=1
    build=sub(model,'build')
    for i,(x,y,z) in build_ids:sub(build,'item',objectid=i,transform=f'1 0 0 0 1 0 0 0 1 {x} {y} {z}')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
        z.writestr('Metadata/model_settings.config',ET.tostring(config,encoding='utf-8',xml_declaration=True))
        settings={'filament_colour':[COLORS[c] for c in names],'filament_type':['PLA']*len(names),'filament_settings_id':['Generic PLA @BBL A1']*len(names),'filament_diameter':['1.75']*len(names),'filament_density':['1.24']*len(names)}
        z.writestr('Metadata/project_settings.config',json.dumps(settings))

clip=Point(0,0).buffer(COIN_RADIUS,quad_segs=128)
ring=clip.difference(Point(0,0).buffer(28.6,quad_segs=128))
coin_text_size=5.4
coin_text_weight=.07
front_number=text('#73559',coin_text_size,0,-23.15).buffer(coin_text_weight)
front_title=arc('POTATO DUCKS',24.2,coin_text_size).buffer(coin_text_weight)
back_title=arc('FIRST LEGO LEAGUE',23.4,coin_text_size).buffer(coin_text_weight)
back_team=text('TEAM',coin_text_size,0,-16.8).buffer(coin_text_weight)
assert min(g.distance(ring) for g in (front_title,back_title,back_team))>.3
assert back_team.distance(front_number)>.5
assert front_number.distance(ring)>.3
assert front_number.distance(unary_union([g for _,g in mascot()]))>.4
front=regions([('gold',ring),('gold',front_title),*mascot(),('gold',front_number)],clip)
# Reverse: a large three-toed webbed duck footprint, with no personal dedication.
foot=poly([(-2,-9),(-5,-3),(-10,4),(-9,7),(-5,5),(-2,6),(0,11),(2,6),(5,5),(9,7),(10,4),(5,-3),(2,-9)]).buffer(.45)
foot_details=unary_union([stroke([(0,-7),(-6.8,4.6)],.65),stroke([(0,-7),(0,7.8)],.65),stroke([(0,-7),(6.8,4.6)],.65)])
back=regions([('gold',ring),('gold',back_title),('black',foot.buffer(.65)),('orange',foot),('black',foot_details),('yellow',back_team),('yellow',front_number)],clip)
# Standalone flat-backed, thick mascot relief, 62 mm tall, plus display stand.
raw=mascot();sil=unary_union([g for c,g in raw]).buffer(.65)
minx,miny,maxx,maxy=sil.bounds
factor=62/(maxy-miny)
raw=[(c,translate(scale(g,xfact=factor,yfact=factor,origin=(0,0)),0,-miny*factor+6)) for c,g in raw]
sil=translate(scale(sil,xfact=factor,yfact=factor,origin=(0,0)),0,-miny*factor+6)
tab=box(-5,0,5,8)
sil=unary_union([sil,tab]);masreg=regions(raw,sil)
models={'coin_front':make_meshes(front,clip),'coin_back':make_meshes(back,clip),'mascot_relief':make_meshes(masreg,sil,base=3.2,face=.8)}
# Separate dowels keep both decorated halves flat on the print bed.
# Left-to-right flipping preserves Y; unequal diameters key the upright orientation.
pin_specs=[(10,2.0),(-10,1.4)]
pin_height=1.6
socket_depth=1.0
radial_clearance=.22
socket_outline=unary_union([ellipse(0,y,r+radial_clearance,r+radial_clearance) for y,r in pin_specs])
socket_tool=extrude(socket_outline,-.2,socket_depth+.2)
assert pin_height<2*socket_depth<2*BASE
assert pin_specs[0][1]>pin_specs[1][1]+radial_clearance
for name in ('coin_front','coin_back'):
    before=models[name]['navy']
    models[name]['navy']=trimesh.boolean.difference([before,socket_tool],engine='manifold')
    print(name,'socket removed volume',before.volume-models[name]['navy'].volume,'expected',socket_outline.area*socket_depth)
pins=extrude(unary_union([ellipse(0,y,r,r) for y,r in pin_specs]),0,pin_height)
assert pins.is_watertight and pins.is_winding_consistent and len(pins.split())==2
(ROOT/'models'/'stl'/'coin_alignment').mkdir(parents=True,exist_ok=True)
pins.export(ROOT/'models'/'stl'/'coin_alignment'/'coin_alignment_pins.stl')
# Stand slot takes the 4.0 mm tab with 0.3 mm clearance in both axes.
standshape=box(-18,-11,18,11).buffer(3).buffer(-3)
stand=extrude(standshape,0,8)
slot_outline=box(-5.15,-2.15,5.15,2.15)
slot=extrude(slot_outline,2,7)
stand_label=text('#73559',5.4,0,-6.5)
assert standshape.buffer(-1).covers(stand_label) and not slot_outline.intersects(stand_label)
stand=trimesh.boolean.difference([stand,slot,extrude(stand_label,7.2,1.6)],engine='manifold')
models['mascot_stand']={'navy':stand}
report={'units':'mm','coin_diameter':60,'coin_half_thickness':2.4,'assembled_coin_thickness':4.8,'checks':[],'notes':['Not physically test printed.','Mascot is a thick flat-backed relief with a separate stand, not a fully sculpted figurine.','Coin halves use two separate unequal dowels and glue back-to-back.']}
for name,meshes in models.items():
    folder=ROOT/'models'/'stl'/name;folder.mkdir(parents=True,exist_ok=True)
    for color,m in meshes.items():
        assert m.is_watertight and m.is_winding_consistent and m.volume>0,(name,color)
        f=folder/(name+'_'+color+'.stl');m.export(f)
        reload=trimesh.load_mesh(f,process=True)
        assert reload.is_watertight and reload.is_winding_consistent
        report['checks'].append({'part':name+'_'+color,'watertight':bool(reload.is_watertight),'winding_consistent':bool(reload.is_winding_consistent),'volume_mm3':round(m.volume,3),'triangles':len(m.faces),'bounds_mm':m.bounds.round(3).tolist()})
    if name!='mascot_stand':
        reg,outline,bh,fh={'coin_front':(front,clip,BASE,FACE),'coin_back':(back,clip,BASE,FACE),'mascot_relief':(masreg,sil,3.2,.8)}[name]
        outline=set_precision(outline,0.001)
        pairs=[reg[a].intersection(reg[b]).area for a in reg for b in reg if a<b]
        overlap=max(pairs,default=0)
        uncovered=outline.difference(unary_union(list(reg.values()))).area
        assert overlap<.005 and uncovered<.001,(name,overlap,uncovered)
        expected=outline.area*(bh+fh)
        if name.startswith('coin_'): expected-=socket_outline.area*socket_depth
        error=abs(sum(m.volume for m in meshes.values())-expected)
        assert error<(1.1 if name.startswith('coin_') else .5),(name,error)
        # Constant-height relief has exactly the outline extrusion as its fused solid.
        # Construct it directly: boolean union of coplanar color walls is numerically unstable.
        union=extrude(outline,0,bh+fh)
        if name.startswith('coin_'): union=trimesh.boolean.difference([union,socket_tool],engine='manifold')
        report[name]={'fused_watertight':bool(union.is_watertight),'max_color_overlap_area_mm2':overlap,'uncovered_area_mm2':uncovered,'volume_error_mm3':error,'connected_components':len(union.split()),'dimensions_mm':union.extents.round(3).tolist()}
    else:
        union=meshes['navy']
        report[name]={'fused_watertight':bool(union.is_watertight),'connected_components':len(union.split()),'dimensions_mm':union.extents.round(3).tolist()}
    assert union.is_watertight and len(union.split())==1,name
    # Monochrome fallback has all touching regions fused.
    (ROOT/'models'/'stl'/'monochrome').mkdir(exist_ok=True)
    union.export(ROOT/'models'/'stl'/'monochrome'/(name+'_fused.stl'))
    write3mf(ROOT/'models'/'3mf'/(name+'_6color.3mf'),[(name,meshes,(65,65,0))])
write3mf(ROOT/'models'/'3mf'/'coin_pair_6color.3mf',[('coin_front',models['coin_front'],(40,40,0)),('coin_back',models['coin_back'],(106,40,0))])
write3mf(ROOT/'models'/'3mf'/'coin_pair_4color_AMS.3mf',[('coin_front',models['coin_front'],(40,40,0)),('coin_back',models['coin_back'],(106,40,0))],four=True)
write3mf(ROOT/'models'/'3mf'/'mascot_and_stand_6color.3mf',[('mascot_relief',models['mascot_relief'],(60,25,0)),('mascot_stand',models['mascot_stand'],(60,112,0))])
write3mf(ROOT/'print/coin'/'coin_alignment_pins.3mf',[('coin_alignment_pins',{'navy':pins},(65,65,0))],four=True)
report['coin_alignment']={'pin_diameters_mm':[4,2.8],'pin_height_mm':pin_height,'socket_depth_mm':socket_depth,'radial_clearance_mm':radial_clearance,'pins_watertight':bool(pins.is_watertight)}
(ROOT/'validation'/'geometry_validation.json').write_text(json.dumps(report,indent=2))
fig,axs=plt.subplots(1,4,figsize=(18,5),facecolor='#F4F1E9')
for ax,reg,title in zip(axs,[front,back,masreg],['60 mm coin • front','60 mm coin • reverse','62 mm mascot relief + mounting tab']):draw(ax,reg,title)
draw(axs[3],{'navy':standshape.difference(slot_outline.union(stand_label))},'Stand • engraved #73559')
fig.suptitle('POTATO DUCKS  •  TEAM #73559',fontsize=19,color='#172840',weight='bold');fig.tight_layout(rect=(0,0,1,.90));fig.savefig(ROOT/'docs'/'design_preview.png',dpi=180,facecolor=fig.get_facecolor());plt.close(fig)
# Editable vector design accompanies parametric source.
fig,axs=plt.subplots(1,2,figsize=(10,5))
for ax,reg,title in zip(axs,[front,back],['Front','Reverse']):draw(ax,reg,title)
fig.savefig(ROOT/'sources'/'coin_artwork.svg');plt.close(fig)
print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2));print('Color STL files:',len(report['checks']))
