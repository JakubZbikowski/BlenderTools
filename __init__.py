import bpy
from . import search_by_volume

def register():
    search_by_volume.register()

def unregister():
    search_by_volume.unregister()


if __name__ == "__main__":
    register()
