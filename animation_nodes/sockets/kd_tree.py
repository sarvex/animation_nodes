import bpy
from mathutils.kdtree import KDTree
from .. base_types import AnimationNodeSocket

class KDTreeSocket(bpy.types.NodeSocket, AnimationNodeSocket):
    bl_idname = "an_KDTreeSocket"
    bl_label = "KDTree Socket"
    dataType = "KDTree"
    drawColor = (0.32, 0.32, 0.18, 1)
    comparable = True
    storable = True

    @classmethod
    def getDefaultValue(cls):
        kdTree = KDTree(0)
        kdTree.balance()
        return kdTree

    @classmethod
    def correctValue(cls, value):
        return (value, 0) if isinstance(value, KDTree) else (cls.getDefaultValue(), 2)
