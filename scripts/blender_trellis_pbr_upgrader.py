"""
KARARSIZLIK — TRELLIS.2 .glb Modelleri Icin Otomatik AAA Karanlik PBR & Kristal Yukseltici
Blender 4.2+ / 5.x (RTX GPU / Cycles OptiX uyumlu)

Kullanim:
1. Blender'da File -> Import -> glTF 2.0 (.glb) ile TRELLIS.2 modelini iceri aktar.
2. Scripting sekmesine gec -> New -> Bu kodu yapistir -> Run Script (Ucgen Play) tusuna bas.
3. Layout ekraninda Z tusuna basip 'Rendered' secerek gercek isin izlemeli PBR kalitesini gor.
"""

import bpy


def upgrade_trellis_to_dark_pbr(
    saturation=0.78,
    value=0.75,
    metallic_strength=0.92,
    bump_strength=0.35,
    emission_strength=3.5,
    setup_studio_lights=True,
):
    # 1. RTX Ray-Tracing (Cycles GPU) + Karanlik Atmosfer
    scene = bpy.context.scene
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

    # 2. Sahnedeki Tum Mesh'leri Puruzsuzlestir ve Gercek PBR Materyale Cevir
    meshes = [o for o in scene.objects if o.type == 'MESH']
    for obj in meshes:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try:
            bpy.ops.object.shade_auto_smooth()
        except Exception:
            bpy.ops.object.shade_smooth()

        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes:
                continue
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
            tex_node = next((n for n in nodes if n.type == 'TEX_IMAGE'), None)

            if bsdf and tex_node:
                # Soguk ve kirli karanlik ortacag renk dengesi
                hsv = nodes.new('ShaderNodeHueSaturation')
                hsv.inputs['Saturation'].default_value = saturation
                hsv.inputs['Value'].default_value = value
                links.new(tex_node.outputs['Color'], hsv.inputs['Color'])
                links.new(hsv.outputs['Color'], bsdf.inputs['Base Color'])

                # Kristal / buyu bolgelerini doygunluktan (HSV) otomatik ayir
                sep = nodes.new('ShaderNodeSeparateColor')
                sep.mode = 'HSV'
                links.new(tex_node.outputs['Color'], sep.inputs['Color'])

                sat_ramp = nodes.new('ShaderNodeValToRGB')
                sat_ramp.color_ramp.elements[0].position = 0.28
                sat_ramp.color_ramp.elements[1].position = 0.50
                links.new(sep.outputs[1], sat_ramp.inputs['Fac'])

                # Metalik harita: Kristal kisimlar metalik degil, demir/bronz govde gercek metalik
                inv = nodes.new('ShaderNodeMath')
                inv.operation = 'SUBTRACT'
                inv.inputs[0].default_value = 1.0
                links.new(sat_ramp.outputs['Color'], inv.inputs[1])

                metal_mul = nodes.new('ShaderNodeMath')
                metal_mul.operation = 'MULTIPLY'
                metal_mul.inputs[1].default_value = metallic_strength
                links.new(inv.outputs['Value'], metal_mul.inputs[0])
                links.new(metal_mul.outputs['Value'], bsdf.inputs['Metallic'])

                # Roughness (Matlik/Parlaklik varyasyonu) + Mikro dovme celik kabartmasi (Bump)
                rough_ramp = nodes.new('ShaderNodeValToRGB')
                rough_ramp.color_ramp.elements[0].color = (0.52, 0.52, 0.52, 1)
                rough_ramp.color_ramp.elements[1].color = (0.18, 0.18, 0.18, 1)
                links.new(sep.outputs[2], rough_ramp.inputs['Fac'])
                links.new(rough_ramp.outputs['Color'], bsdf.inputs['Roughness'])

                bump = nodes.new('ShaderNodeBump')
                bump.inputs['Strength'].default_value = bump_strength
                bump.inputs['Distance'].default_value = 0.02
                links.new(sep.outputs[2], bump.inputs['Height'])
                links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

                # Buyu/Kristal ic parlamasi (Emission)
                if 'Emission Color' in bsdf.inputs:
                    links.new(tex_node.outputs['Color'], bsdf.inputs['Emission Color'])
                    glow_mul = nodes.new('ShaderNodeMath')
                    glow_mul.operation = 'MULTIPLY'
                    glow_mul.inputs[1].default_value = emission_strength
                    links.new(sat_ramp.outputs['Color'], glow_mul.inputs[0])
                    links.new(glow_mul.outputs['Value'], bsdf.inputs['Emission Strength'])

    # 3. 3 Noktali Sinematik Karanlik Fantastik Isiklandirma
    if setup_studio_lights:
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

    print("KARARSIZLIK Sinematik PBR Kurulumu Tamamlandi!")


if __name__ == "__main__":
    upgrade_trellis_to_dark_pbr()
