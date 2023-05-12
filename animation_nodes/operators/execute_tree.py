import bpy
from bpy.props import *
from .. problems import canExecute
from .. utils.blender_ui import redrawAll

class ExecuteNodeTree(bpy.types.Operator):
    bl_idname = "an.execute_tree"
    bl_label = "Execute Node Tree"
    bl_description = "Execute all main networks in the tree"

    name: StringProperty(name = "Node Tree Name")

    @classmethod
    def poll(cls, context):
        return canExecute()

    def execute(self, context):
        nodeTree = bpy.data.node_groups.get(self.name)
        if nodeTree is not None and nodeTree.bl_idname == "an_AnimationNodeTree":
            nodeTree.execute()
            redrawAll()
            return {"FINISHED"}
        self.report({"ERROR"}, f"{repr(self.name)} is no animation nodes tree")
        return {"CANCELLED"}
