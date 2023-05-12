import bpy
from .. utils.blender_ui import PieMenuHelper

class SelectionPie(bpy.types.Menu, PieMenuHelper):
    bl_idname = "AN_MT_selection_pie"
    bl_label = "Selection Pie"

    @classmethod
    def poll(cls, context):
        tree = context.getActiveAnimationNodeTree()
        return False if tree is None else tree.nodes.active is not None

    def drawLeft(self, layout):
        layout.operator("an.select_dependencies")

    def drawRight(self, layout):
        layout.operator("an.select_dependent_nodes")

    def drawBottom(self, layout):
        layout.operator("an.select_network")

    def drawTop(self, layout):
        layout.operator("an.frame_active_network")
