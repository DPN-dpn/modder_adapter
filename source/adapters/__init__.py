from . import xxmi_tools, blender_dds_addon

modules = [
    xxmi_tools,
    blender_dds_addon,
]

def register():
    for mod in modules:
        if hasattr(mod, "register"):
            mod.register()

def unregister():
    for mod in reversed(modules):
        if hasattr(mod, "unregister"):
            mod.unregister()