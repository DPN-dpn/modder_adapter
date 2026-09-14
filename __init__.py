# Blender 애드온 정보
bl_info = {
    "name": "모더 어댑터",
    "author": "DPN",
    "version": (1, 0, 1),
    "blender": (2, 80, 0),
    "location": "환경설정(Preferences) > 애드온(Add-ons)",
    "description": "xxmi 모딩 중 불편한 점들을 해결하기 위한 자잘한 기능 지원",
    "category": "System",
}

from . import source

def register():
    source.register()

def unregister():
    source.unregister()

if __name__ == "__main__":
    register()
