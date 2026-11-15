"""
KARARSIZLIK / EMPEROR OF ASH — TRELLIS.2 .glb Modelleri Icin Otomatik AAA Karanlik PBR Yukseltici (v2.0)
Blender 4.2+ / 5.x Uyumlu

Profiller (`profile` parametresi):
- 'METAL_CRYSTAL': Kilic, hancer, zirh, metal esyalar (Dovme celik + mor kristal parlama)
- 'STONE_RUIN'   : Imparator heykeli, kopru, tas yapilar (0.0 Metalik, mat isli tas + guclu kabartma)
- 'WOOD_LEATHER' : Yay, ok, deri kiyafet, ahsap esyalar (0.0 Metalik, dogal puruzluluk, 0 parlama)

ONEMLI UNREAL ENGINE 5.8 NOTU:
glTF/.glb ve .fbx formatlari Blender icindeki prosedurel dugum zincirlerini (SeparateColor/ColorRamp) dogrudan
oyun motoruna tasimaz; yalnizca gomulu BaseColor dokusunu tasir. Bu yuzden Unreal Engine 5.8 icinde bir kez
`M_Kararsizlik_Master` materyali kurulur ve gelen tum modellere Material Instance (`MI_Metal`, `MI_Stone`, `MI_Wood`)
atanarak ayni gorunum oyun icinde gercek zamanli elde edilir!
"""

import bpy


def upgrade_trellis_to_dark_pbr(
    profile="METAL_CRYSTAL",  # 'METAL_CRYSTAL' | 'STONE_RUIN' | 'WOOD_LEATHER'
    saturation=0.78,
    value=0.75,
    metallic_strength=0.92,
    bump_strength=0.35,
    emission_strength=3.5,
    setup_studio_lights=True,
):
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
            mat.use_backface_culling = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
            tex_node = next((n for n in nodes if n.type == 'TEX_IMAGE'), None)

            if bsdf and tex_node:
                for old_n in [n for n in list(nodes) if n not in (bsdf, tex_node) and n.type != 'OUTPUT_MATERIAL']:
                    nodes.remove(old_n)

                hsv = nodes.new('ShaderNodeHueSaturation')
                hsv.inputs['Saturation'].default_value = saturation if profile != "STONE_RUIN" else 0.65
                hsv.inputs['Value'].default_value = value
                links.new(tex_node.outputs['Color'], hsv.inputs['Color'])
                links.new(hsv.outputs['Color'], bsdf.inputs['Base Color'])

                sep = nodes.new('ShaderNodeSeparateColor')
                sep.mode = 'HSV'
                links.new(tex_node.outputs['Color'], sep.inputs['Color'])

                if profile == "METAL_CRYSTAL":
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
                    metal_mul.inputs[1].default_value = metallic_strength
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
                        glow_mul.inputs[1].default_value = emission_strength
                        links.new(sat_ramp.outputs['Color'], glow_mul.inputs[0])
                        links.new(glow_mul.outputs['Value'], bsdf.inputs['Emission Strength'])

                elif profile == "STONE_RUIN":
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
                bump.inputs['Strength'].default_value = min(1.0, bump_strength * (1.4 if profile == "STONE_RUIN" else 1.0))
                bump.inputs['Distance'].default_value = 0.02
                links.new(sep.outputs[2], bump.inputs['Height'])
                links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

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
        add_light("MoonRimLight", (-2.0, 1.5, 1.5), 65.0, (0.65, 0.45, 1.0), 1.2)
        add_light("WarmEmberFill", (-1.5, -1.8, -0.5), 25.0, (1.0, 0.65, 0.4), 1.5)

    print(f"KARARSIZLIK Sinematik PBR ({profile}) Kurulumu Tamamlandi!")


if __name__ == "__main__":
    upgrade_trellis_to_dark_pbr(profile="METAL_CRYSTAL")
