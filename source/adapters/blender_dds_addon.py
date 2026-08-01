import bpy
from bpy.props import BoolProperty
import os

def _apply_dds_adapter():
    try:
        import blender_dds_addon
        import blender_dds_addon.directx.texconv
        import blender_dds_addon.ui.import_dds
        import blender_dds_addon.ui.bpy_util
    except ImportError:
        return
        
    Texconv = blender_dds_addon.directx.texconv.Texconv
    import_dds_module = blender_dds_addon.ui.import_dds
    
    # 2. put_import_options 래핑 (UI 추가)
    if not hasattr(import_dds_module, "_mdad_orig_put_import_options"):
        import_dds_module._mdad_orig_put_import_options = import_dds_module.put_import_options
        
        def _mdad_put_import_options(context, layout):
            import_dds_module._mdad_orig_put_import_options(context, layout)
            layout.prop(context.window_manager, "mdad_dds_ignore_alpha")
            layout.prop(context.window_manager, "mdad_dds_create_material")
            
        import_dds_module.put_import_options = _mdad_put_import_options
        
    # 2.5 load_dds 래핑 (머테리얼 생성 로직)
    if not hasattr(import_dds_module, "_mdad_orig_load_dds"):
        import_dds_module._mdad_orig_load_dds = import_dds_module.load_dds
        
        def _mdad_load_dds(file, invert_normals=False, premultiplied_alpha=False, cubemap_layout='h-cross', colorspace_ldr='sRGB', colorspace_hdr='Non-Color', texconv=None, astcenc=None):
            tex = import_dds_module._mdad_orig_load_dds(file, invert_normals=invert_normals, premultiplied_alpha=premultiplied_alpha, cubemap_layout=cubemap_layout, colorspace_ldr=colorspace_ldr, colorspace_hdr=colorspace_hdr, texconv=texconv, astcenc=astcenc)
            
            if getattr(bpy.context.window_manager, "mdad_dds_create_material", False) and tex:
                mat_name = os.path.basename(file).split(".")[0]
                mat = bpy.data.materials.get(mat_name)
                if not mat:
                    mat = bpy.data.materials.new(name=mat_name)
                
                mat.use_nodes = True
                
                # BSDF 노드 찾기
                bsdf = None
                for node in mat.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        bsdf = node
                        break
                        
                if bsdf:
                    # 기존 이미지 텍스처 노드가 있으면 재사용하거나 새로 생성
                    tex_image = None
                    for node in mat.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image == tex:
                            tex_image = node
                            break
                            
                    if not tex_image:
                        tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
                        tex_image.image = tex
                        tex_image.location = (bsdf.location.x - 300, bsdf.location.y)
                        
                    mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
                    mat.node_tree.links.new(bsdf.inputs['Alpha'], tex_image.outputs['Alpha'])
                    
                    mat.blend_method = 'HASHED'

            return tex
            
        import_dds_module.load_dds = _mdad_load_dds
        
    # 3. load_uncompressed_dds 래핑
    if not hasattr(import_dds_module, "_mdad_orig_load_uncompressed_dds"):
        import_dds_module._mdad_orig_load_uncompressed_dds = import_dds_module.load_uncompressed_dds
        
        def _mdad_load_uncompressed_dds(file, cubemap_layout='h-cross', premultiplied_alpha=False, color_space='Non-Color'):
            tex = import_dds_module._mdad_orig_load_uncompressed_dds(file, cubemap_layout=cubemap_layout, premultiplied_alpha=premultiplied_alpha, color_space=color_space)
            
            if getattr(bpy.context.window_manager, "mdad_dds_ignore_alpha", False):
                import tempfile
                from blender_dds_addon.ui.bpy_util import save_texture, load_texture
                with tempfile.TemporaryDirectory() as temp_dir:
                    jpg = os.path.join(temp_dir, os.path.basename(file)[:-4] + '.jpg')
                    save_texture(tex, jpg, 'JPEG')
                    color_space_str = getattr(tex.colorspace_settings, 'name', color_space)
                    new_tex = load_texture(jpg, name=os.path.basename(jpg)[:-4], color_space=color_space_str)
                    bpy.data.images.remove(tex)
                    return new_tex
            return tex
            
        import_dds_module.load_uncompressed_dds = _mdad_load_uncompressed_dds

    # 4. load_dds_via_tga 래핑
    if not hasattr(import_dds_module, "_mdad_orig_load_dds_via_tga"):
        import_dds_module._mdad_orig_load_dds_via_tga = import_dds_module.load_dds_via_tga
        
        def _mdad_load_dds_via_tga(texconv, file, out_dir, cubemap_layout='h-cross', invert_normals=False, premultiplied_alpha=False, color_space='Non-Color'):
            tex = import_dds_module._mdad_orig_load_dds_via_tga(texconv, file, out_dir, cubemap_layout=cubemap_layout, invert_normals=invert_normals, premultiplied_alpha=premultiplied_alpha, color_space=color_space)
            
            if getattr(bpy.context.window_manager, "mdad_dds_ignore_alpha", False):
                import tempfile
                from blender_dds_addon.ui.bpy_util import save_texture, load_texture
                with tempfile.TemporaryDirectory() as temp_dir:
                    jpg = os.path.join(temp_dir, os.path.basename(file)[:-4] + '.jpg')
                    save_texture(tex, jpg, 'JPEG')
                    color_space_str = getattr(tex.colorspace_settings, 'name', color_space)
                    new_tex = load_texture(jpg, name=os.path.basename(jpg)[:-4], color_space=color_space_str)
                    bpy.data.images.remove(tex)
                    return new_tex
            return tex
                
        import_dds_module.load_dds_via_tga = _mdad_load_dds_via_tga


def _remove_dds_adapter():
    try:
        import blender_dds_addon.ui.import_dds
        import blender_dds_addon.directx.texconv
        
        import_dds_module = blender_dds_addon.ui.import_dds
        Texconv = blender_dds_addon.directx.texconv.Texconv
        
        if hasattr(import_dds_module, "_mdad_orig_put_import_options"):
            import_dds_module.put_import_options = import_dds_module._mdad_orig_put_import_options
            delattr(import_dds_module, "_mdad_orig_put_import_options")
            
        if hasattr(import_dds_module, "_mdad_orig_load_dds"):
            import_dds_module.load_dds = import_dds_module._mdad_orig_load_dds
            delattr(import_dds_module, "_mdad_orig_load_dds")
            
        if hasattr(import_dds_module, "_mdad_orig_load_uncompressed_dds"):
            import_dds_module.load_uncompressed_dds = import_dds_module._mdad_orig_load_uncompressed_dds
            delattr(import_dds_module, "_mdad_orig_load_uncompressed_dds")
            
        if hasattr(import_dds_module, "_mdad_orig_load_dds_via_tga"):
            import_dds_module.load_dds_via_tga = import_dds_module._mdad_orig_load_dds_via_tga
            delattr(import_dds_module, "_mdad_orig_load_dds_via_tga")
            
    except Exception:
        pass


def get_adapter_status():
    status = {
        "name": "Blender DDS Add-on",
        "addon_found": False,
        "adapter_attached": False,
    }
    try:
        import blender_dds_addon
        import blender_dds_addon.ui.import_dds
        status["addon_found"] = True
        
        import_dds_module = blender_dds_addon.ui.import_dds
        if hasattr(import_dds_module, "_mdad_orig_load_uncompressed_dds"):
            status["adapter_attached"] = True
    except Exception:
        pass
    return status


def register():
    if not hasattr(bpy.types.WindowManager, "mdad_dds_ignore_alpha"):
        bpy.types.WindowManager.mdad_dds_ignore_alpha = BoolProperty(
            name="Ignore Alpha",
            description="Ignore alpha channel and import image as fully opaque",
            default=True,
        )
    if not hasattr(bpy.types.WindowManager, "mdad_dds_create_material"):
        bpy.types.WindowManager.mdad_dds_create_material = BoolProperty(
            name="Create Material",
            description="Automatically create a material for the imported DDS",
            default=True,
        )
    _apply_dds_adapter()


def unregister():
    _remove_dds_adapter()
    if hasattr(bpy.types.WindowManager, "mdad_dds_ignore_alpha"):
        del bpy.types.WindowManager.mdad_dds_ignore_alpha
    if hasattr(bpy.types.WindowManager, "mdad_dds_create_material"):
        del bpy.types.WindowManager.mdad_dds_create_material
