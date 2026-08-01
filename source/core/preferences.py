import bpy
from bpy.props import StringProperty, BoolProperty
from ..adapters import xxmi_tools, blender_dds_addon

def addon_module_name():
    # Use the top-level package/module name so bl_idname matches the addon module
    try:
        return __name__.split(".")[0]
    except Exception:
        return __name__


class EVBHPreferences(bpy.types.AddonPreferences):
    bl_idname = addon_module_name()

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        latest_version = scene.get("mdad.latest_version", "")
        current_version = scene.get("mdad.current_version", "")
        update_available = scene.get("mdad.update_available", False)
        show_restart = scene.get("mdad.show_restart", False)

        # 버튼 라벨 조건 분기
        if not latest_version:
            update_label = "업데이트 체크 필요"
        elif not update_available:
            update_label = "현재 최신 버전입니다"
        else:
            update_label = f"업데이트: {current_version} → {latest_version}"

        layout.operator("mdad.check_update", text="업데이트 체크", icon="FILE_REFRESH")
        row = layout.row()
        if show_restart:
            row.operator(
                "wm.quit_blender", text="블렌더 종료(애드온 재실행)", icon="CANCEL"
            )
        else:
            row.enabled = bool(update_available)
            row.operator("mdad.do_update", text=update_label, icon="IMPORT")
        layout.operator("mdad.open_github", text="GitHub", icon="URL")
        layout.operator("evbh.open_wiki", text="Wiki", icon="HELP")

        layout.separator()
        layout.label(text="어댑터 연동 상태", icon="PLUGIN")
        
        box = layout.box()
        # XXMI Tools
        xxmi_status = xxmi_tools.get_adapter_status()
        row = box.row()
        row.label(text=xxmi_status["name"], icon="MESH_DATA")
        
        if xxmi_status["addon_found"]:
            if xxmi_status["adapter_attached"]:
                row.label(text="정상 연동됨", icon="CHECKMARK")
            else:
                row.label(text="연동 실패 (애드온 재실행 권장)", icon="ERROR")
        else:
            row.label(text="애드온 미설치 또는 비활성화", icon="X")
            
        # Blender DDS Add-on
        dds_status = blender_dds_addon.get_adapter_status()
        row = box.row()
        row.label(text=dds_status["name"], icon="IMAGE_DATA")
        
        if dds_status["addon_found"]:
            if dds_status["adapter_attached"]:
                row.label(text="정상 연동됨", icon="CHECKMARK")
            else:
                row.label(text="연동 실패 (애드온 재실행 권장)", icon="ERROR")
        else:
            row.label(text="애드온 미설치 또는 비활성화", icon="X")

classes = (EVBHPreferences,)


def register():

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
