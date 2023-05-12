import bpy
from ... base_types import AnimationNode

class TextBlockReaderNode(AnimationNode, bpy.types.Node):
    bl_idname = "an_TextBlockReaderNode"
    bl_label = "Text Block Reader"

    def create(self):
        self.newInput("Text Block", "Text Block", "textBlock", defaultDrawType = "PROPERTY_ONLY")
        self.newOutput("Text", "Text", "text")

    def execute(self, textBlock):
        return "" if textBlock is None else textBlock.as_string()
