"""
KARARSIZLIK — ComfyUI -> Blender (PBR + Yumusatma + Isik) -> Onayli Unreal Engine 5.8.4Kopru Eklentisi
Blender 4.2+ / 5.x Uyumlu (N-Panel: 'KARARSIZLIK' sekmesi ekler!)

Kurulum (Sadece 1 Kere Yapilir):
1. Blender'da Edit -> Preferences -> Add-ons -> Sag ustteki kucuk ok -> 'Install from Disk...' tikla.
2. Bu dosyayi (kararsizlik_pipeline_bridge.py) secip kur ve kutucuguna tik at.
3. 3D ekranda klavyeden 'N' tusuna bas -> Sagda acilan dikey menude 'KARARSIZLIK' sekmesine tikla!

Kullanim:
- [1. ADIM] 'Son ComfyUI Modelini Getir + PBR + Yumusat' butonuna bas:
  ComfyUI output\3d klasorundeki EN SON urettigin .glb modelini otomatik bulur, sahneyi temizler,
  iceri alir, ipek gibi yumusatir, kararmis celik + parlayan mor kristal PBR materyali ve stüdyo isigini kurar!
- Modeli incele, begenirsen:
- [2. ADIM - ONAY] 'ONAYLA -> Unreal Engine'e Gonder' butonuna bas:
  Modelin merkezini/boyutunu oyun motoruna uygun hale getirir ve dogrudan Unreal Engine Auto-Import klasorune atar!
"""

bl_info = {
    "name": "KARARSIZLIK: ComfyUI -> Blender -> Unreal 5.8 Koprusu",
    "author": "KARARSIZLIK Dev Team",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar (N) > KARARSIZLIK",
    "description": "ComfyUI TRELLIS.2 .glb ciktisini otomatik alir, karanlik PBR + yumusatma uygular ve onayla Unreal Engine 5.8'e aktarir.",
    "category": "Import-Export",
}

import os
import glob
import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty
from bpy.types import Operator, Panel, PropertyGroup


# Varsayilan ComfyUI TRELLIS.2 cikti klasoru (kullanicinin bilgisayarindaki tam yol)
DEFAULT_COMFY_3D_DIR = r"C:\Users\efezz\AppData\Local\Comfy-Desktop\ComfyUI-Shared\output\3d"
DEFAULT_UE_IMPORT_DIR = r"C:\KARARSIZLIK_UnrealBridge\AutoImport"


class KARARSIZLIK_Properties(PropertyGroup):
    comfy_dir: StringProperty(
        name="ComfyUI 3D Klasoru",
        description="TRELLIS.2 .glb dosyalarinin ciktigi klasor",
        default=DEFAULT_COMFY_3D_DIR,
        subtype='DIR_PATH',
    )
    unreal_dir: StringProperty(
        name="Unreal Auto-Import Klasoru",
        description="Onaylanan modellerin Unreal Engine 5.8 icin kaydedilecegi klasor",
        default=DEFAULT_UE_IMPORT_DIR,
        subtype='DIR_PATH',
    )
    asset_name: StringProperty(
        name="Esya / Model Adi",
        description="Unreal Engine'e giderken verilecek temiz dosya adi (orn: SM_Karanlik_Idol)",
        default="SM_Kararsizlik_Asset",
    )
    smooth_iterations: IntProperty(
        name="Yumusatma Gucu",
        description="Corrective Smooth tekrar sayisi (0 = kapali, 10 = ideal ipek yumusatma)",
        default=8,
        min=0,
        max=40,
    )
    metallic_strength: FloatProperty(
        name="Metalik Keskinlik",
        default=0.92,
        min=0.0,
        max=1.0,
    )
    bump_strength: FloatProperty(
        name="Dovme Demir Kabartma",
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
        name="Akici Oyun Motoru Onizlemesi (EEVEE - Camurlasma Yok)",
        description="Aciksa EEVEE gercek zamanli akici mod kullanir; kapaliysa Cycles sinema isin izleme kullanir",
        default=True,
    )


def apply_dark_pbr_and_smooth(context, props):
    scene = context.scene

    # Render motoru ayari (Camurlasmayan EEVEE veya Sinematik Cycles)
    if props.use_eevee_realtime:
        # Blender 4.2+ / 5.x EEVEE Next / EEVEE ismi kontrolu
        eevee_id = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE'
        scene.render.engine = eevee_id
    else:
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'GPU'
        scene.cycles.samples = 128

    # Karanlik atmosfer arka plani
    world = scene.world or bpy.data.worlds.new("DarkWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.012, 0.012, 0.016, 1.0)
        bg.inputs[1].default_value = 0.6

    meshes = [o for o in scene.objects if o.type == 'MESH']
    for obj in meshes:
        context.view_layer.objects.active = obj
        obj.select_set(True)

        # 1. Otomatik Yumusatma (Corrective Smooth)
        if props.smooth_iterations > 0:
            mod = obj.modifiers.get("KARARSIZLIK_SMOOTH") or obj.modifiers.new(
                name="KARARSIZLIK_SMOOTH", type='CORRECTIVE_SMOOTH'
            )
            mod.iterations = props.smooth_iterations
            mod.smooth_type = 'LENGTH_WEIGHTED'
            mod.use_only_smooth = True

        try:
            bpy.ops.object.shade_auto_smooth()
        except Exception:
            bpy.ops.object.shade_smooth()

        # 2. Karanlik Metal + Parlayan Mor Kristal PBR Materyal Yukseltmesi
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes:
                continue
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
            tex_node = next((n for n in nodes if n.type == 'TEX_IMAGE'), None)

            if bsdf and tex_node:
                # Eski dugumler varsa temiz tutmak icin kontrol et
                hsv = nodes.new('ShaderNodeHueSaturation')
                hsv.inputs['Saturation'].default_value = 0.78
                hsv.inputs['Value'].default_value = 0.75
                links.new(tex_node.outputs['Color'], hsv.inputs['Color'])
                links.new(hsv.outputs['Color'], bsdf.inputs['Base Color'])

                sep = nodes.new('ShaderNodeSeparateColor')
                sep.mode = 'HSV'
                links.new(tex_node.outputs['Color'], sep.inputs['Color'])

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

                bump = nodes.new('ShaderNodeBump')
                bump.inputs['Strength'].default_value = props.bump_strength
                bump.inputs['Distance'].default_value = 0.02
                links.new(sep.outputs[2], bump.inputs['Height'])
                links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

                if 'Emission Color' in bsdf.inputs:
                    links.new(tex_node.outputs['Color'], bsdf.inputs['Emission Color'])
                    glow_mul = nodes.new('ShaderNodeMath')
                    glow_mul.operation = 'MULTIPLY'
                    glow_mul.inputs[1].default_value = props.emission_strength
                    links.new(sat_ramp.outputs['Color'], glow_mul.inputs[0])
                    links.new(glow_mul.outputs['Value'], bsdf.inputs['Emission Strength'])

    # 3. 3 Noktali Sinematik Karanlik Isiklandirma
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

    add_light("ColdKeyLight", (1.8, -2.0, 2.2), 85.0, (0.78, 0.86, 1.0), 1.8)
    add_light("PurpleRimLight", (-2.0, 1.5, 1.5), 65.0, (0.65, 0.35, 1.0), 1.2)
    add_light("WarmEmberFill", (-1.5, -1.8, -0.5), 25.0, (1.0, 0.65, 0.4), 1.5)

    # Viewport'u otomatik Rendered moduna gecir
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'RENDERED'


class KARARSIZLIK_OT_ImportLatestComfy(Operator):
    """ComfyUI klasorundeki EN SON uretilen .glb modeli bulur, sahneye alir, yumusatir ve PBR isik kurar"""
    bl_idname = "kararsizlik.import_latest_comfy"
    bl_label = "1. Son ComfyUI Modelini Getir + PBR + Yumusat"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.kararsizlik_props
        folder = bpy.path.abspath(props.comfy_dir)

        if not os.path.isdir(folder):
            self.report({'ERROR'}, f"Klasor bulunamadi: {folder}")
            return {'CANCELLED'}

        glb_files = glob.glob(os.path.join(folder, "*.glb")) + glob.glob(os.path.join(folder, "**", "*.glb"), recursive=True)
        if not glb_files:
            self.report({'ERROR'}, f"Bu klasorde hic .glb dosyasi yok: {folder}")
            return {'CANCELLED'}

        latest_glb = max(glb_files, key=os.path.getmtime)
        base_name = os.path.splitext(os.path.basename(latest_glb))[0]
        props.asset_name = f"SM_{base_name}"

        # Eski objeleri temizle (Isiklar ve Mesh'ler)
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

        # En yeni .glb modelini iceri aktar
        bpy.ops.import_scene.gltf(filepath=latest_glb)

        # PBR + Yumusatma + Isik uygula
        apply_dark_pbr_and_smooth(context, props)

        self.report({'INFO'}, f"Yuklendi ve hazirlandi: {os.path.basename(latest_glb)} -> Simdi inceleyip onaylayabilirsin!")
        return {'FINISHED'}


class KARARSIZLIK_OT_ApproveExportUnreal(Operator):
    """Onaylanan modeli temizleyip Unreal Engine 5.8 Auto-Import klasorune aktarir"""
    bl_idname = "kararsizlik.approve_export_unreal"
    bl_label = "2. ONAYLA -> Unreal Engine 5.8'e Gonder!"
    bl_options = {'REGISTER'}

    def execute(self, context):
        props = context.scene.kararsizlik_props
        export_dir = bpy.path.abspath(props.unreal_dir)
        os.makedirs(export_dir, exist_ok=True)

        meshes = [o for o in context.scene.objects if o.type == 'MESH']
        if not meshes:
            self.report({'ERROR'}, "Sahnede aktarilacak 3D model yok!")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        for obj in meshes:
            context.view_layer.objects.active = obj
            obj.select_set(True)
            # Modifier'lari (yumusatmayi) kalici uygula
            for mod in list(obj.modifiers):
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except Exception:
                    pass
            # Rotasyon ve olcegi Unreal icin sifirla
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        clean_name = props.asset_name.strip() or "SM_Kararsizlik_Asset"
        out_glb = os.path.join(export_dir, f"{clean_name}.glb")

        # Unreal Engine 5.8 glTF/GLB dogrudan PBR + Texture ile kusursuz alir!
        bpy.ops.export_scene.gltf(
            filepath=out_glb,
            export_format='GLB',
            use_selection=True,
            export_apply=True,
        )

        self.report({'INFO'}, f"ONAYLANDI! Unreal Engine klasorune gonderildi: {out_glb}")
        return {'FINISHED'}


class KARARSIZLIK_PT_MainPanel(Panel):
    bl_label = "KARARSIZLIK 3D Koprusu"
    bl_idname = "KARARSIZLIK_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "KARARSIZLIK"

    def draw(self, context):
        layout = self.layout
        props = context.scene.kararsizlik_props

        box = layout.box()
        box.label(text="Klasor Yollari:", icon='FILE_FOLDER')
        box.prop(props, "comfy_dir", text="Comfy 3D")
        box.prop(props, "unreal_dir", text="UE5 Klasor")

        box2 = layout.box()
        box2.label(text="Kalite & Yumusatma Ayarlari:", icon='MOD_SMOOTH')
        box2.prop(props, "use_eevee_realtime")
        box2.prop(props, "smooth_iterations")
        box2.prop(props, "metallic_strength")
        box2.prop(props, "bump_strength")
        box2.prop(props, "emission_strength")

        layout.separator()
        col = layout.column(align=True)
        col.scale_y = 1.6
        col.operator("kararsizlik.import_latest_comfy", icon='IMPORT')

        layout.separator()
        box3 = layout.box()
        box3.label(text="Inceledin ve Begendiysen:", icon='CHECKMARK')
        box3.prop(props, "asset_name", text="UE5 Ismi")
        col2 = box3.column(align=True)
        col2.scale_y = 1.8
        col2.operator("kararsizlik.approve_export_unreal", icon='EXPORT')


classes = (
    KARARSIZLIK_Properties,
    KARARSIZLIK_OT_ImportLatestComfy,
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
