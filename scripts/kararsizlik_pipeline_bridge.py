"""
KARARSIZLIK / EMPEROR OF ASH — ComfyUI -> Blender -> Onayli Unreal Engine 5.8.4 Kopru Eklentisi (v2.0.0)
Blender 4.2+ / 5.x Uyumlu (N-Panel: 'KARARSIZLIK' sekmesi)

v2.0.0 Muhendislik Iyilestirmeleri:
1. Materyal Profilleri (Metal+Kristal / Tas+Harabe / Ahsap+Deri+Organik) — Tas heykelleri metal yapmaz!
2. Otomatik Pivot (Origin) & Gercek Boyut (Metre) Standardi:
   - Zemin Objesi / Heykel: Origin = Alt Taban Merkezi (Z=0)
   - Silah / Kilic / Hancer: Origin = Kabza Tutma Noktasi (Alttan %22 yukarisi, hand_rSocket uyumlu!)
   - Merkez: Origin = Geometri Merkezi
3. Poligon Butcesi (Decimate) & Otomatik Unreal `UCX_` Convex Carpısma Kutusu Uretici!
4. Tek Tarafli Manifold Yuzey Kontrolu (`use_backface_culling = True` secenegi + opsiyonel Solidify)
5. Unreal Engine 5.8 Aktarimda:
   - Hem `FBX` (`UCX_` collision ile UE5 standardi) hem `GLB` destekli,
   - Onaylanan temizlenmis modeli `ApprovedStaging` ve `AutoImport` klasorlerine kaydeder (MCP sunucusu ham modeli degil, bu temiz modeli kullanir!),
   - Not: Prosedurel PBR gorunumu UE5 tarafinda `M_Kararsizlik_Master` materyali ile birebir eslesir.
"""

bl_info = {
    "name": "KARARSIZLIK: ComfyUI -> Blender -> Unreal 5.8 Koprusu",
    "author": "KARARSIZLIK Dev Team",
    "version": (2, 3, 2),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar (N) > KARARSIZLIK",
    "description": "UV-Koruyucu Sifir-Beneklenme PBR (0.1 sn!), Evrensel Renk ve Unreal 5.8 koprusu.",
    "category": "Import-Export",
}

import bmesh
import glob
import json
import os
import bpy
from mathutils import Vector
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup


def _load_default_paths():
    cfg_candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "kararsizlik_config.json"),
        r"C:\KARARSIZLIK_Fabrika\kararsizlik_config.json",
    ]
    for p in cfg_candidates:
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return (
                    data.get("comfy_3d_output", r"C:\Users\efezz\AppData\Local\Comfy-Desktop\ComfyUI-Shared\output\3d"),
                    data.get("unreal_autoimport_dir", r"D:\UE5_Projects\EmperorOfAsh_Bridge\AutoImport"),
                    data.get("approved_staging_dir", r"D:\UE5_Projects\EmperorOfAsh_Bridge\ApprovedStaging"),
                )
            except Exception:
                pass
    return (
        r"C:\Users\efezz\AppData\Local\Comfy-Desktop\ComfyUI-Shared\output\3d",
        r"D:\UE5_Projects\EmperorOfAsh_Bridge\AutoImport",
        r"D:\UE5_Projects\EmperorOfAsh_Bridge\ApprovedStaging",
    )


DEFAULT_COMFY_3D_DIR, DEFAULT_UE_IMPORT_DIR, DEFAULT_STAGING_DIR = _load_default_paths()
_LAST_WATCHED_MTIME = 0.0


class KARARSIZLIK_Properties(PropertyGroup):
    comfy_dir: StringProperty(
        name="ComfyUI 3D Klasoru",
        default=DEFAULT_COMFY_3D_DIR,
        subtype='DIR_PATH',
    )
    unreal_dir: StringProperty(
        name="Unreal Auto-Import Klasoru",
        default=DEFAULT_UE_IMPORT_DIR,
        subtype='DIR_PATH',
    )
    asset_name: StringProperty(
        name="Esya / Model Adi",
        default="SM_Kararsizlik_Asset",
    )
    material_profile: EnumProperty(
        name="Materyal Profili",
        description="Modelin orijinal rengini koruyan evrensel fiziksel PBR profilleri (Konsept esyaya bagimli degildir!)",
        items=[
            ('UNIVERSAL_ORIGINAL', "Evrensel Orijinal PBR (Varsayilan — Her Model!)", "Modelin kendi rengine hic dokunmaz (1.0 sadakat), dogal puruzluluk ve kabartma verir"),
            ('PURE_METAL', "Saf Ortacag Metali (Kilic / Zirh / Kalkan — Parlamasiz)", "Deri kabza ile celik namluyu ayirir, yapay parlama EKLEMEZ, kendi renginde gercek celik yapar"),
            ('STONE_RUIN', "Tas / Harabe / Heykel", "Sifir metalik, dogal mat tas puruzlulugu ve guclu yuzey kabartmasi"),
            ('WOOD_LEATHER', "Ahsap / Deri / Kiyafet / Karakter", "Sifir metalik, sifir parlama, dogal organik yuzey"),
            ('ARCANE_GLOW', "Buyulu / Kristalli Esya (Ozel Renk Parlamali)", "Modelin uzerindeki doygun renkteki rün/kristal kisimlarini kendi renginde parlatir"),
        ],
        default='UNIVERSAL_ORIGINAL',
    )
    pivot_preset: EnumProperty(
        name="Pivot (Tutma / Merkez) Noktasi",
        description="Unreal Engine soket ve zemin yerlesimi icin otomatik merkez noktasi",
        items=[
            ('BOTTOM_GROUND', "Zemin Objesi (Alt Taban Z=0 — Heykel/Yapi)", "Modeli tam zemine oturtur, pivot alt taban merkezindedir"),
            ('WEAPON_GRIP', "Silah Kabzasi (Alttan %22 — Kilic/Hancer)", "hand_rSocket tutusu icin pivotu kabza bolgesine alir"),
            ('CENTER', "Tam Merkez (Yay / Kalkan / Kucuk Esya)", "Geometri merkezine hizalar"),
        ],
        default='BOTTOM_GROUND',
    )
    target_height_m: FloatProperty(
        name="Gercek Boyut / Yukseklik (Metre)",
        description="0 birakirsan boyuta dokunmaz; orn: Hancer=0.45, Kilic=1.15, Karakter=1.80, Heykel=3.20",
        default=0.0,
        min=0.0,
        max=50.0,
    )
    target_tris: IntProperty(
        name="Maks Poligon (Bin Ucgen, 0=Dokunma)",
        description="Nanite olmayan silah/zirhlar icin poligon butcesi (orn: Silah=12 -> 12.000 ucgen, Heykel=0 Nanite)",
        default=0,
        min=0,
        max=500,
    )
    generate_ucx_collision: BoolProperty(
        name="Otomatik UCX_ Carpısma Kutusu Uret (FBX)",
        description="Unreal Engine'in otomatik tanidigi basit disbukey (Convex Hull) UCX_ carpısma modeli olusturur",
        default=True,
    )
    export_format_choice: EnumProperty(
        name="Unreal Cikti Formati",
        items=[
            ('FBX_AND_GLB', "FBX (UCX Carpismali) + GLB", "Hem UE5 standart FBX+UCX hem dokulu GLB uretir"),
            ('GLB_ONLY', "Sadece GLB", "Hizli glTF 2.0 ciktisi"),
        ],
        default='FBX_AND_GLB',
    )
    smooth_iterations: IntProperty(
        name="Yumusatma Gucu (Smooth)",
        default=6,
        min=0,
        max=40,
    )
    seam_weld_distance: FloatProperty(
        name="Catlak Kaynatma (0 = Kapali / UV Koru!)",
        description="0 birakirsan UV dokulari %100 korunur ve ASLA siyah benek yapmaz! Sadece doku icermeyen duz modellerde ac",
        default=0.0,
        min=0.0,
        max=0.005,
        precision=5,
    )
    double_sided_preview: BoolProperty(
        name="Cift Tarafli Yuzey (Siyah Bosluklari Kapat)",
        description="Ters donmus ince yuzeylerin arkadan seffaf/catlak gorunmesini onler (UE5 Two-Sided eslenigi)",
        default=True,
    )
    solidify_thickness: FloatProperty(
        name="Ince Yuzey Kalinlastirma (0=Kapali)",
        description="Pelerin/yaprak gibi kagit inceliginde tek tarafli yuzey varsa kalinlik verir (orn: 0.004)",
        default=0.0,
        min=0.0,
        max=0.1,
    )
    color_saturation: FloatProperty(
        name="Renk Doygunlugu (1.0 = Orijinal)",
        description="1.0 modelin kendi orijinal rengidir; biraz daha soluk karanlik atmosfer istersen 0.85 yapabilirsin",
        default=1.0,
        min=0.2,
        max=1.5,
    )
    metallic_strength: FloatProperty(
        name="Metalik Keskinlik",
        default=0.88,
        min=0.0,
        max=1.0,
    )
    bump_strength: FloatProperty(
        name="Yuzey Kabartma (Bump)",
        default=0.30,
        min=0.0,
        max=1.0,
    )
    emission_strength: FloatProperty(
        name="Kristal / Buyu Parlamasi",
        default=3.5,
        min=0.0,
        max=20.0,
    )
    use_eevee_realtime: BoolProperty(
        name="Akici Oyun Motoru Onizlemesi (EEVEE)",
        default=True,
    )
    auto_watch_active: BoolProperty(
        name="Canli Klasor Izleyici Aktif",
        default=False,
    )


def apply_pivot_and_scale(obj, props):
    """TRELLIS.2 rastgele boyut ve merkezini Unreal Engine standartlarina hizalar."""
    if obj.type != 'MESH':
        return
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    # Isiklarin (NeutralKeyLight vb.) secili kalip transform_apply hatasi vermesini %100 onle!
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    bbox_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_x = min(v.x for v in bbox_world)
    max_x = max(v.x for v in bbox_world)
    min_y = min(v.y for v in bbox_world)
    max_y = max(v.y for v in bbox_world)
    min_z = min(v.z for v in bbox_world)
    max_z = max(v.z for v in bbox_world)

    height = max_z - min_z
    if props.target_height_m > 0.001 and height > 1e-5:
        scale_factor = props.target_height_m / height
        obj.scale = (scale_factor, scale_factor, scale_factor)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bbox_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        min_x, max_x = min(v.x for v in bbox_world), max(v.x for v in bbox_world)
        min_y, max_y = min(v.y for v in bbox_world), max(v.y for v in bbox_world)
        min_z, max_z = min(v.z for v in bbox_world), max(v.z for v in bbox_world)

    cx = 0.5 * (min_x + max_x)
    cy = 0.5 * (min_y + max_y)
    if props.pivot_preset == 'BOTTOM_GROUND':
        cz = min_z
    elif props.pivot_preset == 'WEAPON_GRIP':
        cz = min_z + 0.22 * (max_z - min_z)
    else:
        cz = 0.5 * (min_z + max_z)

    saved_cursor = bpy.context.scene.cursor.location.copy()
    bpy.context.scene.cursor.location = Vector((cx, cy, cz))
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    obj.location = Vector((0.0, 0.0, 0.0))
    bpy.context.scene.cursor.location = saved_cursor


def repair_trellis_cracks_and_normals(obj, weld_ratio: float, force: bool = False):
    """
    UV-KORUYUCU SIFIR-BENEKLENME C++ BMesh Duzeltici:
    1) weld_ratio == 0 ise UV dikis yerlerine HIC dokunmaz (Sifir siyah benek!), SADECE gomulu kirik Custom Split Normals'i temizler!
    2) weld_ratio > 0 verilirse Edit Mode'a girmeden 0.1 saniyede kaynatir.
    """
    if obj.type != 'MESH' or obj.name.startswith("UCX_"):
        return

    last_repaired = obj.get("_kararsizlik_repaired_ratio", -1.0)
    if not force and abs(last_repaired - weld_ratio) < 1e-7:
        return

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    try:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    except Exception:
        pass

    if weld_ratio <= 1e-6:
        obj["_kararsizlik_repaired_ratio"] = 0.0
        return

    local_bbox = [Vector(corner) for corner in obj.bound_box]
    diag = (
        Vector((max(v.x for v in local_bbox), max(v.y for v in local_bbox), max(v.z for v in local_bbox)))
        - Vector((min(v.x for v in local_bbox), min(v.y for v in local_bbox), min(v.z for v in local_bbox)))
    ).length
    safe_dist = max(1e-6, diag * max(0.00005, min(0.003, weld_ratio)))

    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=safe_dist)
        bm.normal_update()
        bm.to_mesh(obj.data)
        obj.data.update()
        obj["_kararsizlik_repaired_ratio"] = float(weld_ratio)
    except Exception as exc:
        print(f"[KARARSIZLIK Hizli BMesh Uyarisi] {exc}")
    finally:
        bm.free()


def apply_dark_pbr_and_smooth(context, props, run_mesh_repair: bool = False):
    scene = context.scene

    if props.use_eevee_realtime:
        eevee_id = (
            'BLENDER_EEVEE_NEXT'
            if 'BLENDER_EEVEE_NEXT' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys()
            else 'BLENDER_EEVEE'
        )
        scene.render.engine = eevee_id
    else:
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'GPU'
        scene.cycles.samples = 128

    world = scene.world or bpy.data.worlds.new("DarkWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.012, 0.012, 0.016, 1.0)
        bg.inputs[1].default_value = 0.6

    meshes = [o for o in scene.objects if o.type == 'MESH' and not o.name.startswith("UCX_")]
    for obj in meshes:
        context.view_layer.objects.active = obj
        obj.select_set(True)

        # 0. HIZLI BMesh CATLAK TAMIRI (Sadece ilk yuklemede veya kaynatma mesafesi degistiginde 0.1 sn calisir!)
        repair_trellis_cracks_and_normals(obj, props.seam_weld_distance, force=run_mesh_repair)

        # Modelin boyuna uygun guvenli Weld esigi
        local_bbox = [Vector(corner) for corner in obj.bound_box]
        diag = max(
            0.01,
            (
                Vector((max(v.x for v in local_bbox), max(v.y for v in local_bbox), max(v.z for v in local_bbox)))
                - Vector((min(v.x for v in local_bbox), min(v.y for v in local_bbox), min(v.z for v in local_bbox)))
            ).length,
        )

        # 1. Corrective Smooth (Agir Weld Modifier tekrarini kaldirdik cunku BMesh zaten tek seferde dikti!)
        if "KARARSIZLIK_WELD" in obj.modifiers:
            obj.modifiers.remove(obj.modifiers["KARARSIZLIK_WELD"])

        if props.smooth_iterations > 0:
            mod = obj.modifiers.get("KARARSIZLIK_SMOOTH") or obj.modifiers.new(
                name="KARARSIZLIK_SMOOTH", type='CORRECTIVE_SMOOTH'
            )
            mod.iterations = props.smooth_iterations
            mod.smooth_type = 'SIMPLE'
            mod.use_only_smooth = True
            mod.use_pin_boundary = True
        elif "KARARSIZLIK_SMOOTH" in obj.modifiers:
            obj.modifiers.remove(obj.modifiers["KARARSIZLIK_SMOOTH"])

        # Opsiyonel Solidify (Tek tarafli ince yuzeyler icin gercek manifold kalinlik)
        if props.solidify_thickness > 0.0001:
            sol = obj.modifiers.get("KARARSIZLIK_SOLIDIFY") or obj.modifiers.new(
                name="KARARSIZLIK_SOLIDIFY", type='SOLIDIFY'
            )
            sol.thickness = min(props.solidify_thickness, diag * 0.02)
        elif "KARARSIZLIK_SOLIDIFY" in obj.modifiers:
            obj.modifiers.remove(obj.modifiers["KARARSIZLIK_SOLIDIFY"])

        # Eski agir Weighted Normal varsa temizle (Yuksek poligonda EEVEE ile birlesince takilma yapiyordu)
        if "KARARSIZLIK_WNORMAL" in obj.modifiers:
            obj.modifiers.remove(obj.modifiers["KARARSIZLIK_WNORMAL"])

        # Opsiyonel Poligon Butcesi (Decimate — Dikkat: Doku ve ince geometrileri kirmamasi icin varsayilan 0 tutun!)
        current_tris = len(obj.data.polygons)
        target_tri_count = props.target_tris * 1000
        if target_tri_count > 0 and current_tris > target_tri_count:
            dec = obj.modifiers.get("KARARSIZLIK_DECIMATE") or obj.modifiers.new(
                name="KARARSIZLIK_DECIMATE", type='DECIMATE'
            )
            dec.ratio = max(0.05, min(1.0, target_tri_count / float(current_tris)))
        elif "KARARSIZLIK_DECIMATE" in obj.modifiers:
            obj.modifiers.remove(obj.modifiers["KARARSIZLIK_DECIMATE"])

        # Tam Shade Smooth (Aninda calisir, sifir siyah cizgi!)
        bpy.ops.object.shade_smooth()

        # 2. Materyal Profiline Gore Fiziksel Dogru PBR Onizleme (UE5 M_Kararsizlik_Master eslenigi!)
        profile = props.material_profile
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes:
                continue
            # Cift tarafli secenek aciksa ince pelerin/sac/kivrim arkadan siyah bosluk gibi gorunmez!
            mat.use_backface_culling = not props.double_sided_preview
            if hasattr(mat, "blend_method"):
                mat.blend_method = 'OPAQUE'
            if hasattr(mat, "surface_render_method"):
                mat.surface_render_method = 'DITHERED'

            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
            tex_node = next((n for n in nodes if n.type == 'TEX_IMAGE'), None)

            if bsdf and tex_node:
                for old_n in [n for n in list(nodes) if n not in (bsdf, tex_node) and n.type != 'OUTPUT_MATERIAL']:
                    nodes.remove(old_n)

                # Orijinal renk koruma (1.0 varsayilan — konsept esyaya bagimli renk kaydirma YOK!)
                hsv = nodes.new('ShaderNodeHueSaturation')
                hsv.inputs['Saturation'].default_value = props.color_saturation
                hsv.inputs['Value'].default_value = 1.0
                links.new(tex_node.outputs['Color'], hsv.inputs['Color'])
                links.new(hsv.outputs['Color'], bsdf.inputs['Base Color'])

                sep = nodes.new('ShaderNodeSeparateColor')
                sep.mode = 'HSV'
                links.new(tex_node.outputs['Color'], sep.inputs['Color'])

                if profile == 'UNIVERSAL_ORIGINAL':
                    # Her modelde (karakter, silah, tas, ahsap) bozmadan calisan evrensel dogal PBR
                    bsdf.inputs['Metallic'].default_value = 0.08
                    if 'Emission Strength' in bsdf.inputs:
                        bsdf.inputs['Emission Strength'].default_value = 0.0
                    rough_ramp = nodes.new('ShaderNodeValToRGB')
                    rough_ramp.color_ramp.elements[0].color = (0.72, 0.72, 0.72, 1)
                    rough_ramp.color_ramp.elements[1].color = (0.35, 0.35, 0.35, 1)
                    links.new(sep.outputs[2], rough_ramp.inputs['Fac'])
                    links.new(rough_ramp.outputs['Color'], bsdf.inputs['Roughness'])

                elif profile == 'PURE_METAL':
                    # Parlamasiz gercek ortacag celigi: Renkli/sicak deri kabzayi mat tutar, renksiz celigi metal yapar!
                    if 'Emission Strength' in bsdf.inputs:
                        bsdf.inputs['Emission Strength'].default_value = 0.0
                    sat_ramp = nodes.new('ShaderNodeValToRGB')
                    sat_ramp.color_ramp.elements[0].position = 0.22
                    sat_ramp.color_ramp.elements[1].position = 0.45
                    links.new(sep.outputs[1], sat_ramp.inputs['Fac'])

                    inv = nodes.new('ShaderNodeMath')
                    inv.operation = 'SUBTRACT'
                    inv.inputs[0].default_value = 1.0
                    links.new(sat_ramp.outputs['Color'], inv.inputs[1])

                    metal_mul = nodes.new('ShaderNodeMath')
                    metal_mul.operation = 'MULTIPLY'
                    metal_mul.inputs[1].default_value = props.metallic_strength
                    links.new(inv.outputs['Value'], metal_mul.inputs[0])
                    links.new(metal_mul.outputs['Value'], bsdf.inputs['Metallic'])

                    rough_ramp = nodes.new('ShaderNodeValToRGB')
                    rough_ramp.color_ramp.elements[0].color = (0.55, 0.55, 0.55, 1)
                    rough_ramp.color_ramp.elements[1].color = (0.20, 0.20, 0.20, 1)
                    links.new(sep.outputs[2], rough_ramp.inputs['Fac'])
                    links.new(rough_ramp.outputs['Color'], bsdf.inputs['Roughness'])

                elif profile == 'ARCANE_GLOW':
                    # Hangi renkte kristal/rün varsa (kirmizi, mavi, altin, mor) KENDI RENGINDE parlatir!
                    sat_ramp = nodes.new('ShaderNodeValToRGB')
                    sat_ramp.color_ramp.elements[0].position = 0.28
                    sat_ramp.color_ramp.elements[1].position = 0.50
                    links.new(sep.outputs[1], sat_ramp.inputs['Fac'])

                    inv = nodes.new('ShaderNodeMath')
                    inv.operation = 'SUBTRACT'
                    inv.inputs[0].default_value = 1.0
                    links.new(sat_ramp.outputs['Color'], inv.inputs[1])

                    metal_mul = nodes.new('ShaderNodeMath')
                    metal_mul.operation = 'MULTIPLY'
                    metal_mul.inputs[1].default_value = props.metallic_strength
                    links.new(inv.outputs['Value'], metal_mul.inputs[0])
                    links.new(metal_mul.outputs['Value'], bsdf.inputs['Metallic'])

                    rough_ramp = nodes.new('ShaderNodeValToRGB')
                    rough_ramp.color_ramp.elements[0].color = (0.52, 0.52, 0.52, 1)
                    rough_ramp.color_ramp.elements[1].color = (0.18, 0.18, 0.18, 1)
                    links.new(sep.outputs[2], rough_ramp.inputs['Fac'])
                    links.new(rough_ramp.outputs['Color'], bsdf.inputs['Roughness'])

                    if 'Emission Color' in bsdf.inputs:
                        links.new(tex_node.outputs['Color'], bsdf.inputs['Emission Color'])
                        glow_mul = nodes.new('ShaderNodeMath')
                        glow_mul.operation = 'MULTIPLY'
                        glow_mul.inputs[1].default_value = props.emission_strength
                        links.new(sat_ramp.outputs['Color'], glow_mul.inputs[0])
                        links.new(glow_mul.outputs['Value'], bsdf.inputs['Emission Strength'])

                elif profile == 'STONE_RUIN':
                    bsdf.inputs['Metallic'].default_value = 0.0
                    if 'Emission Strength' in bsdf.inputs:
                        bsdf.inputs['Emission Strength'].default_value = 0.0
                    rough_ramp = nodes.new('ShaderNodeValToRGB')
                    rough_ramp.color_ramp.elements[0].color = (0.88, 0.88, 0.88, 1)
                    rough_ramp.color_ramp.elements[1].color = (0.62, 0.62, 0.62, 1)
                    links.new(sep.outputs[2], rough_ramp.inputs['Fac'])
                    links.new(rough_ramp.outputs['Color'], bsdf.inputs['Roughness'])

                else:  # WOOD_LEATHER
                    bsdf.inputs['Metallic'].default_value = 0.0
                    if 'Emission Strength' in bsdf.inputs:
                        bsdf.inputs['Emission Strength'].default_value = 0.0
                    rough_ramp = nodes.new('ShaderNodeValToRGB')
                    rough_ramp.color_ramp.elements[0].color = (0.76, 0.76, 0.76, 1)
                    rough_ramp.color_ramp.elements[1].color = (0.45, 0.45, 0.45, 1)
                    links.new(sep.outputs[2], rough_ramp.inputs['Fac'])
                    links.new(rough_ramp.outputs['Color'], bsdf.inputs['Roughness'])

                bump = nodes.new('ShaderNodeBump')
                bump_val = props.bump_strength * (1.4 if profile == 'STONE_RUIN' else 1.0)
                bump.inputs['Strength'].default_value = min(1.0, bump_val)
                bump.inputs['Distance'].default_value = 0.02
                links.new(sep.outputs[2], bump.inputs['Height'])
                links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    # 3. 3 Noktali Notr Sinematik Studyo Isiklandirmasi (Sifir Mor Boyama — %100 Gercek Renk!)
    for o in [obj for obj in scene.objects if obj.type == 'LIGHT']:
        bpy.data.objects.remove(o, do_unlink=True)

    def add_light(name, loc, energy, color, size):
        light_data = bpy.data.lights.new(name=name, type='AREA')
        light_data.energy = energy
        light_data.color = color
        light_data.size = size
        light_obj = bpy.data.objects.new(name=name, object_data=light_data)
        scene.collection.objects.link(light_obj)
        light_obj.location = loc
        direction = -light_obj.location
        light_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    add_light("NeutralKeyLight", (1.8, -2.0, 2.2), 85.0, (0.96, 0.98, 1.0), 1.8)
    add_light("CoolMoonRimLight", (-2.0, 1.5, 1.5), 55.0, (0.78, 0.86, 1.0), 1.2)
    add_light("SoftWarmFill", (-1.5, -1.8, -0.5), 22.0, (1.0, 0.88, 0.75), 1.5)

    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'RENDERED'


def _fast_latest_glb_mtime(folder: str):
    best_mtime = 0.0
    best_path = None
    if not os.path.isdir(folder):
        return best_mtime, best_path
    try:
        with os.scandir(folder) as it:
            for entry in it:
                if entry.is_file() and entry.name.lower().endswith(".glb"):
                    st = entry.stat()
                    if st.st_mtime > best_mtime and st.st_size > 1024:
                        best_mtime = st.st_mtime
                        best_path = entry.path
    except OSError:
        pass
    return best_mtime, best_path


def create_ucx_convex_collision(context, target_obj, clean_name: str):
    """Unreal Engine FBX standardina uygun `UCX_<MeshName>` hafif disbukey carpısma kabugu uretir."""
    for old_ucx in [o for o in context.scene.objects if o.name.startswith("UCX_")]:
        bpy.data.objects.remove(old_ucx, do_unlink=True)

    ucx_mesh = target_obj.data.copy()
    ucx_obj = bpy.data.objects.new(f"UCX_{clean_name}", ucx_mesh)
    ucx_obj.matrix_world = target_obj.matrix_world.copy()
    context.scene.collection.objects.link(ucx_obj)

    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = ucx_obj
    ucx_obj.select_set(True)

    # Convex Hull + Agresif Sadelesme (Maks ~64-128 yuzeyli temiz carpısma kutusu)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.convex_hull()
    bpy.ops.object.mode_set(mode='OBJECT')

    dec = ucx_obj.modifiers.new(name="UCX_DECIMATE", type='DECIMATE')
    dec.ratio = 0.08
    bpy.ops.object.modifier_apply(modifier=dec.name)
    ucx_obj.display_type = 'WIRE'
    ucx_obj.data.materials.clear()
    return ucx_obj


class KARARSIZLIK_OT_ImportLatestComfy(Operator):
    bl_idname = "kararsizlik.import_latest_comfy"
    bl_label = "1. Son ComfyUI Modelini Getir + Hazirla"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kararsizlik_props
        folder = bpy.path.abspath(props.comfy_dir)

        if not os.path.isdir(folder):
            self.report({'ERROR'}, f"Klasor bulunamadi: {folder}")
            return {'CANCELLED'}

        _mtime, latest_glb = _fast_latest_glb_mtime(folder)
        if not latest_glb:
            glb_files = glob.glob(os.path.join(folder, "**", "*.glb"), recursive=True)
            if not glb_files:
                self.report({'ERROR'}, f"Bu klasorde hic .glb dosyasi yok: {folder}")
                return {'CANCELLED'}
            latest_glb = max(glb_files, key=os.path.getmtime)

        base_name = os.path.splitext(os.path.basename(latest_glb))[0]
        props.asset_name = f"SM_{base_name}"

        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

        bpy.ops.import_scene.gltf(filepath=latest_glb)

        for obj in [o for o in context.scene.objects if o.type == 'MESH']:
            apply_pivot_and_scale(obj, props)

        apply_dark_pbr_and_smooth(context, props, run_mesh_repair=True)

        self.report({'INFO'}, f"Hazirlandi: {os.path.basename(latest_glb)} ({props.material_profile})")
        return {'FINISHED'}


class KARARSIZLIK_OT_UpdateSettings(Operator):
    bl_idname = "kararsizlik.update_settings"
    bl_label = "Profil / Pivot / Yumusatma Uygula (Yenile)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kararsizlik_props
        for obj in [o for o in context.scene.objects if o.type == 'MESH' and not o.name.startswith("UCX_")]:
            apply_pivot_and_scale(obj, props)
        apply_dark_pbr_and_smooth(context, props, run_mesh_repair=False)
        self.report({'INFO'}, "Materyal profili, pivot ve poligon ayarlari ANINDA guncellendi!")
        return {'FINISHED'}


class KARARSIZLIK_OT_ResetDefaults(Operator):
    """Tek tikla model ve doku bozan sayilari (Decimate 23, Boyut 0.21, UV beneklenme vb.) altin ayarlara sifirlar!"""
    bl_idname = "kararsizlik.reset_defaults"
    bl_label = "Altin Ayarlara Sifirla (Catlak/Benek Cozer)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kararsizlik_props
        props.target_height_m = 0.0
        props.target_tris = 0
        props.color_saturation = 1.0
        props.seam_weld_distance = 0.0
        props.smooth_iterations = 4
        props.solidify_thickness = 0.0
        props.bump_strength = 0.18
        props.double_sided_preview = True
        self.report({'INFO'}, "Altin ayarlar yuklendi! Simdi '1. Son ComfyUI Modelini Getir' tusuna bas.")
        return {'FINISHED'}


class KARARSIZLIK_OT_ToggleAutoWatch(Operator):
    bl_idname = "kararsizlik.toggle_auto_watch"
    bl_label = "Canli Oto-Yakalayiciyi Baslat / Durdur"

    def execute(self, context):
        global _LAST_WATCHED_MTIME
        props = context.scene.kararsizlik_props
        if props.auto_watch_active:
            props.auto_watch_active = False
            self.report({'INFO'}, "KARARSIZLIK Canli Klasor Izleyici durduruldu.")
            return {'FINISHED'}

        folder = bpy.path.abspath(props.comfy_dir)
        _LAST_WATCHED_MTIME = _fast_latest_glb_mtime(folder)[0]
        props.auto_watch_active = True

        if not bpy.app.timers.is_registered(_kararsizlik_watch_timer):
            bpy.app.timers.register(_kararsizlik_watch_timer, first_interval=3.0)

        self.report({'INFO'}, "SIFIR-KASMA CANLI IZLEYICI AKTIF!")
        return {'FINISHED'}


def _kararsizlik_watch_timer():
    global _LAST_WATCHED_MTIME
    scene = getattr(bpy.context, "scene", None)
    if not scene or not hasattr(scene, "kararsizlik_props"):
        return 3.0
    props = scene.kararsizlik_props
    if not props.auto_watch_active:
        return None

    folder = bpy.path.abspath(props.comfy_dir)
    mtime, latest_glb = _fast_latest_glb_mtime(folder)
    if latest_glb and mtime > _LAST_WATCHED_MTIME + 0.5:
        _LAST_WATCHED_MTIME = mtime
        try:
            bpy.ops.kararsizlik.import_latest_comfy()
        except Exception as exc:
            print(f"[KARARSIZLIK Watch] Otomatik yukleme hatasi: {exc}")
    return 3.0


class KARARSIZLIK_OT_ApproveExportUnreal(Operator):
    """Modifier'lari uygular, Pivot/Olcek ve UCX_ carpismasini olusturup hem Staging hem Unreal AutoImport'a aktarir"""
    bl_idname = "kararsizlik.approve_export_unreal"
    bl_label = "2. ONAYLA -> Unreal Engine 5.8'e Gonder!"
    bl_options = {'REGISTER'}

    def execute(self, context):
        props = context.scene.kararsizlik_props
        export_dir = bpy.path.abspath(props.unreal_dir)
        os.makedirs(export_dir, exist_ok=True)
        os.makedirs(DEFAULT_STAGING_DIR, exist_ok=True)

        meshes = [o for o in context.scene.objects if o.type == 'MESH' and not o.name.startswith("UCX_")]
        if not meshes:
            self.report({'ERROR'}, "Sahnede aktarilacak 3D model yok!")
            return {'CANCELLED'}

        clean_name = "".join(c if c.isalnum() or c == "_" else "_" for c in props.asset_name.strip()) or "SM_Kararsizlik_Asset"
        if not clean_name.startswith("SM_"):
            clean_name = f"SM_{clean_name}"

        # Birden fazla parca varsa birlestir ve modifier'lari kalici uygula
        bpy.ops.object.select_all(action='DESELECT')
        for obj in meshes:
            context.view_layer.objects.active = obj
            obj.select_set(True)
            for mod in list(obj.modifiers):
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except Exception:
                    pass

        if len(meshes) > 1:
            context.view_layer.objects.active = meshes[0]
            bpy.ops.object.join()

        main_obj = context.view_layer.objects.active
        main_obj.name = clean_name
        apply_pivot_and_scale(main_obj, props)

        ucx_obj = None
        if props.generate_ucx_collision:
            ucx_obj = create_ucx_convex_collision(context, main_obj, clean_name)

        # Secimi hazirla (Ana model + varsa UCX_)
        bpy.ops.object.select_all(action='DESELECT')
        main_obj.select_set(True)
        if ucx_obj:
            ucx_obj.select_set(True)
        context.view_layer.objects.active = main_obj

        # 1) GLB Ciktisi (Gomulu TRELLIS BaseColor dokusuyla -> Staging ve Unreal klasorune)
        out_glb = os.path.join(export_dir, f"{clean_name}.glb")
        staging_glb = os.path.join(DEFAULT_STAGING_DIR, f"{clean_name}.glb")
        main_only_select = ucx_obj is not None
        if main_only_select:
            ucx_obj.select_set(False)  # glTF icinde UCX ayri gorunur mesh olmasin; UCX FBX icindir!

        for target_glb in (out_glb, staging_glb):
            try:
                bpy.ops.export_scene.gltf(
                    filepath=target_glb,
                    export_format='GLB',
                    use_selection=True,
                    export_apply=True,
                )
            except TypeError:
                bpy.ops.export_scene.gltf(
                    filepath=target_glb,
                    export_format='GLB',
                    use_selection=True,
                )

        # 2) UE 5.8 Standart FBX Ciktisi (Gomulu Doku + UCX_ Convex Carpısma ile!)
        if props.export_format_choice == 'FBX_AND_GLB':
            if ucx_obj:
                ucx_obj.select_set(True)
            out_fbx = os.path.join(export_dir, f"{clean_name}.fbx")
            staging_fbx = os.path.join(DEFAULT_STAGING_DIR, f"{clean_name}.fbx")
            for target_fbx in (out_fbx, staging_fbx):
                bpy.ops.export_scene.fbx(
                    filepath=target_fbx,
                    use_selection=True,
                    apply_scale_options='FBX_SCALE_ALL',
                    axis_forward='-Y',
                    axis_up='Z',
                    mesh_smooth_type='FACE',
                    path_mode='COPY',
                    embed_textures=True,
                )

        if ucx_obj:
            bpy.data.objects.remove(ucx_obj, do_unlink=True)

        self.report(
            {'INFO'},
            f"ONAYLANDI! {clean_name} (Pivot: {props.pivot_preset}, UCX: {props.generate_ucx_collision}) Unreal'a gonderildi! "
            f"(UE5'te M_Kararsizlik_Master materyalini ata!)",
        )
        return {'FINISHED'}


class KARARSIZLIK_PT_MainPanel(Panel):
    bl_label = "KARARSIZLIK 3D Koprusu v2.3.2"
    bl_idname = "KARARSIZLIK_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "KARARSIZLIK"

    def draw(self, context):
        layout = self.layout
        props = context.scene.kararsizlik_props

        box = layout.box()
        box.label(text="Klasor Yollari (D: Uyumlu):", icon='FILE_FOLDER')
        box.prop(props, "comfy_dir", text="Comfy 3D")
        box.prop(props, "unreal_dir", text="UE5 Klasor")

        box_std = layout.box()
        box_std.label(text="UE 5.8 Standart & Profil:", icon='MATERIAL')
        box_std.prop(props, "material_profile", text="Tur")
        box_std.prop(props, "pivot_preset", text="Pivot")
        box_std.prop(props, "target_height_m")
        box_std.prop(props, "target_tris")

        box2 = layout.box()
        box2.label(text="Hizli Catlak Dikici & PBR:", icon='MOD_SMOOTH')
        box2.operator("kararsizlik.reset_defaults", icon='LOOP_BACK')
        box2.prop(props, "use_eevee_realtime")
        box2.prop(props, "double_sided_preview")
        box2.prop(props, "color_saturation")
        box2.prop(props, "seam_weld_distance")
        box2.prop(props, "smooth_iterations")
        box2.prop(props, "solidify_thickness")
        if props.material_profile in ('PURE_METAL', 'ARCANE_GLOW'):
            box2.prop(props, "metallic_strength")
        if props.material_profile == 'ARCANE_GLOW':
            box2.prop(props, "emission_strength")
        box2.prop(props, "bump_strength")
        box2.operator("kararsizlik.update_settings", icon='FILE_REFRESH')

        layout.separator()
        col_watch = layout.column(align=True)
        col_watch.scale_y = 1.3
        watch_label = "🔴 CANLI OTO-YAKALAYICI AKTIF (Durdur)" if props.auto_watch_active else "🟢 Canli Oto-Yakalayiciyi Ac"
        watch_icon = 'PAUSE' if props.auto_watch_active else 'PLAY'
        col_watch.operator("kararsizlik.toggle_auto_watch", text=watch_label, icon=watch_icon, depress=props.auto_watch_active)

        col = layout.column(align=True)
        col.scale_y = 1.6
        col.operator("kararsizlik.import_latest_comfy", icon='IMPORT')

        layout.separator()
        box3 = layout.box()
        box3.label(text="UE 5.8 Onay & Cikti (M_Kararsizlik_Master):", icon='CHECKMARK')
        box3.prop(props, "asset_name", text="UE5 Ismi")
        box3.prop(props, "export_format_choice", text="Format")
        box3.prop(props, "generate_ucx_collision")
        col2 = box3.column(align=True)
        col2.scale_y = 1.8
        col2.operator("kararsizlik.approve_export_unreal", icon='EXPORT')


classes = (
    KARARSIZLIK_Properties,
    KARARSIZLIK_OT_ImportLatestComfy,
    KARARSIZLIK_OT_UpdateSettings,
    KARARSIZLIK_OT_ResetDefaults,
    KARARSIZLIK_OT_ToggleAutoWatch,
    KARARSIZLIK_OT_ApproveExportUnreal,
    KARARSIZLIK_PT_MainPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.kararsizlik_props = bpy.props.PointerProperty(type=KARARSIZLIK_Properties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.kararsizlik_props


if __name__ == "__main__":
    register()
