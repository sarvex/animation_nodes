import bpy
from bpy.props import *
from ... math import composeMatrixList
from ... tree_info import getNodesByType
from ... base_types import AnimationNode, VectorizedSocket
from ... id_keys import keyDataTypeItems, IDKey, findsIDKeys, updateIdKeysList

class ObjectIDKeyNode(AnimationNode, bpy.types.Node):
    bl_idname = "an_ObjectIDKeyNode"
    bl_label = "Object ID Key"
    bl_width_default = 160

    def keyChanged(self, context):
        updateIdKeysList()
        self.refresh()

    searchTags = [("Object Initial Transforms",
                   {"keyDataType" : repr("Transforms"),
                    "keyName" : repr("Initial Transforms")})]

    keyDataType: EnumProperty(name = "Key Data Type", default = "Transforms",
        items = keyDataTypeItems, update = keyChanged)

    keyName: StringProperty(name = "Key Name", default = "",
        update = keyChanged)

    useList: VectorizedSocket.newProperty()

    def create(self):
        self.newInput(VectorizedSocket("Object", "useList",
            ("Object", "object", dict(defaultDrawType = "PROPERTY_ONLY")),
            ("Objects", "objects")))

        if self.keyName == "":
            return

        if self.keyDataType == "Transforms":
            self.newOutput(VectorizedSocket("Vector", "useList",
                ("Location", "location"), ("Locations", "locations")))
            self.newOutput(VectorizedSocket("Euler", "useList",
                ("Rotation", "rotation"), ("Rotations", "rotations")))
            self.newOutput(VectorizedSocket("Vector", "useList",
                ("Scale", "scale"), ("Scales", "scales")))
            self.newOutput(VectorizedSocket("Matrix", "useList",
                ("Matrix", "matrix"), ("Matrices", "matrices")))
        elif self.keyDataType == "Text":
            self.newOutput(VectorizedSocket("Text", "useList",
                ("Text", "text"), ("Texts", "texts")))
        elif self.keyDataType == "Integer":
            self.newOutput(VectorizedSocket("Integer", "useList",
                ("Number", "number"), ("Numbers", "numbers")))
        elif self.keyDataType == "Float":
            self.newOutput(VectorizedSocket("Float", "useList",
                ("Number", "number"), ("Numbers", "numbers")))

        self.newOutput(VectorizedSocket("Boolean", "useList",
            ("Exists", "exists", dict(hide = True)),
            ("Exists", "exists", dict(hide = True))))

    def drawAdvanced(self, layout):
        col = layout.column()
        col.prop(self, "keyDataType", text = "Type")
        col.prop(self, "keyName", text = "Name")

    def draw(self, layout):
        col = layout.column()
        col.scale_y = 1.5
        text = "Choose ID Key" if self.keyName == "" else repr(self.keyName)
        self.invokeSelector(col, "ID_KEY", "assignIDKey",
            text = text, icon = "VIEWZOOM")

    def assignIDKey(self, dataType, name):
        self.keyDataType = dataType
        self.keyName = name

    def getExecutionCode(self, required):
        if len(required) == 0 or self.keyName == "":
            return

        keyName = repr(self.keyName)
        yield f"_key = AN.id_keys.IDKeyTypes[{repr(self.keyDataType)}]"
        if self.useList:
            yield from self.getExecutionCode_List(keyName, required)
        else:
            yield from self.getExecutionCode_Base(keyName, required)

    def getExecutionCode_Base(self, keyName, required):
        dataType = self.keyDataType

        if "exists" in required:
            yield f"exists = _key.exists(object, {keyName})"

        yield f"data = _key.get(object, {keyName})"

        if dataType == "Transforms":
            yield "location, rotation, scale = data"
            if "matrix" in required:
                yield "matrix = AN.utils.math.composeMatrix(location, rotation, scale)"
        elif dataType == "Text":
            yield "text = data"
        elif dataType in ("Integer", "Float"):
            yield "number = data"

    def getExecutionCode_List(self, keyName, required):
        dataType = self.keyDataType

        if "exists" in required:
            yield f"exists = _key.existsList(objects, {keyName})"

        if dataType == "Transforms":
            useMatrices = "matrices" in required
            if "locations" in required or useMatrices:
                yield f"locations = _key.getLocations(objects, {keyName})"
            if "rotations" in required or useMatrices:
                yield f"rotations = _key.getRotations(objects, {keyName})"
            if "scales" in required or useMatrices:
                yield f"scales = _key.getScales(objects, {keyName})"
            if useMatrices:
                yield "matrices = AN.math.composeMatrixList(locations, rotations, scales)"
        elif dataType == "Text":
            if "texts" in required:
                yield f"texts = _key.getList(objects, {keyName})"
        elif dataType in ("Integer", "Float"):
            if "numbers" in required:
                yield f"numbers = _key.getList(objects, {keyName})"

    def getList_Exists(self, objects):
        from animation_nodes.id_keys import doesIDKeyExist
        return [doesIDKeyExist(object, self.keyDataType, self.keyName) for object in objects]

    def delete(self):
        self.keyName = ""
        bpy.ops.an.update_id_keys_list()

@findsIDKeys(removable = False)
def getIDKeysOfNodes():
    return {
        IDKey(node.keyDataType, node.keyName)
        for node in getNodesByType("an_ObjectIDKeyNode")
        if node.keyName != ""
    }
