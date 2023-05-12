import bpy
from bpy.props import *
from ... base_types import AnimationNode

dataTypes = {
    "Object" : "objects",
    "Scene" : "scenes",
    "Collection" : "collections",
    "Text Block" : "texts",
    "Material" : "materials" }

class BlendDataByNameNode(AnimationNode, bpy.types.Node):
    bl_idname = "an_BlendDataByNameNode"
    bl_label = "Data by Name"
    dynamicLabelType = "ALWAYS"

    onlySearchTags = True
    searchTags = [(name + " by Name", {"dataType" : repr(name)}) for name in dataTypes.keys()]

    # Should be set only on node creation
    dataType: StringProperty(name = "Data Type", default = "Object",
        update = AnimationNode.refresh)

    def create(self):
        self.newInput("Text", "Name", "name", defaultDrawType = "PROPERTY_ONLY")
        self.newOutput(self.dataType, self.dataType, "output")

    def drawLabel(self):
        return f"{self.dataType} by Name"

    def getExecutionCode(self, required):
        return f"output = bpy.data.{dataTypes[self.dataType]}.get(name)"
