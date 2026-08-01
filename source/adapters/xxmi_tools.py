import bpy
from bpy.props import BoolProperty
import importlib
import collections


class MDAD_PT_Addon_XXMI(bpy.types.Panel):
    bl_label = "모더 어댑터"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_category = "XXMI"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        if not space:
            return False
        active_op = getattr(space, "active_operator", None)
        if not active_op:
            return False
        # 체크할 수 있도록 기본 bl_idname(문자열)과 RNA 형식을 둘 다 허용
        op_id = getattr(active_op, "bl_idname", "")
        return op_id in (
            "import_mesh.migoto_raw_buffers",
            "IMPORT_MESH_OT_migoto_raw_buffers",
        )

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        layout.prop(wm, "mdad_addon_xxmi_clear_vertex")


classes = (MDAD_PT_Addon_XXMI,)


def _apply_xxmi_adapter():
    try:
        mi = importlib.import_module("XXMITools.migoto.import_ops")
    except Exception:
        return
    if hasattr(mi, "_mdad_orig_import_3dmigoto_vb_ib"):
        return

    mi._mdad_orig_import_3dmigoto_vb_ib = mi.import_3dmigoto_vb_ib

    def _mdad_import_3dmigoto_vb_ib(
        operator,
        context,
        paths,
        flip_texcoord_v: bool = True,
        flip_winding: bool = False,
        flip_mesh: bool = False,
        flip_normal: bool = False,
        axis_forward="-Z",
        axis_up="Y",
        pose_cb_off=[0, 0],
        pose_cb_step=1,
        merge_verts: bool = False,
        tris_to_quads: bool = False,
        clean_loose: bool = False,
    ):
        # 원본 함수 실행
        result = mi._mdad_orig_import_3dmigoto_vb_ib(
            operator,
            context,
            paths,
            flip_texcoord_v=flip_texcoord_v,
            flip_winding=flip_winding,
            flip_mesh=flip_mesh,
            flip_normal=flip_normal,
            axis_forward=axis_forward,
            axis_up=axis_up,
            pose_cb_off=pose_cb_off,
            pose_cb_step=pose_cb_step,
            merge_verts=merge_verts,
            tris_to_quads=tris_to_quads,
            clean_loose=clean_loose,
        )

        # 찌꺼기 버텍스 제거 옵션 체크
        wm = context.window_manager
        if getattr(wm, "mdad_addon_xxmi_clear_vertex", False):
            # 임포트 직후에는 새로 생성된 오브젝트가 선택되어 있음
            target_objs = [obj for obj in context.selected_objects if obj.type == 'MESH']
            
            # 선택된 게 없다면 활성화된 오브젝트라도 확인
            if not target_objs and context.view_layer.objects.active and context.view_layer.objects.active.type == 'MESH':
                target_objs = [context.view_layer.objects.active]
                
            if target_objs:
                import bmesh
                for obj in target_objs:
                    bm = bmesh.new()
                    bm.from_mesh(obj.data)
                    bm.verts.ensure_lookup_table()
                    
                    # 면에 속하지 않은 버텍스 수집
                    loose_verts = [v for v in bm.verts if not v.link_faces]
                    
                    if loose_verts:
                        # 직접 버텍스 삭제 (bmesh.ops 대신 확실한 방법 사용)
                        for v in loose_verts:
                            bm.verts.remove(v)
                            
                        # 메시 업데이트
                        bm.to_mesh(obj.data)
                        obj.data.update()
                        
                    bm.free()

        return result

    mi.import_3dmigoto_vb_ib = _mdad_import_3dmigoto_vb_ib


def _remove_xxmi_adapter():
    try:
        mi = importlib.import_module("XXMITools.migoto.import_ops")
    except Exception:
        return
    if hasattr(mi, "_mdad_orig_import_3dmigoto_vb_ib"):
        mi.import_3dmigoto_vb_ib = mi._mdad_orig_import_3dmigoto_vb_ib
        delattr(mi, "_mdad_orig_import_3dmigoto_vb_ib")

def get_adapter_status():
    status = {
        "name": "XXMI Tools",
        "addon_found": False,
        "adapter_attached": False,
    }
    try:
        mi = importlib.import_module("XXMITools.migoto.import_ops")
        status["addon_found"] = True
        if hasattr(mi, "_mdad_orig_import_3dmigoto_vb_ib"):
            status["adapter_attached"] = True
    except Exception:
        pass
    return status

def register():
    if not hasattr(bpy.types.WindowManager, "mdad_addon_xxmi_clear_vertex"):
        bpy.types.WindowManager.mdad_addon_xxmi_clear_vertex = BoolProperty(
            name="찌꺼기 버텍스 제거",
            description="메시 임포트 후 면(Face)에 연결되지 않은 찌꺼기 버텍스를 제거합니다",
            default=True,
        )
    for cls in classes:
        bpy.utils.register_class(cls)
    _apply_xxmi_adapter()


def unregister():
    _remove_xxmi_adapter()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.WindowManager, "mdad_addon_xxmi_clear_vertex"):
        del bpy.types.WindowManager.mdad_addon_xxmi_clear_vertex
