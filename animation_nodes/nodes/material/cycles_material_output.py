import bpy
from bpy.props import *
from bpy.types import Material
from ... base_types import AnimationNode
from ... utils.enum_items import cacheEnumItems

allowedSocketTypes = {
    "NodeSocketVector" : "an_VectorSocket",
    "NodeSocketColor" : "an_ColorSocket",
    "NodeSocketFloatFactor" : "an_FloatSocket",
    "NodeSocketFloat" : "an_FloatSocket" }


class CyclesMaterialOutputNode(AnimationNode, bpy.types.Node):
    bl_idname = "an_CyclesMaterialOutputNode"
    bl_label = "Cycles Material Output"
    bl_width_default = 160

    def getPossibleSocketItems(self, context):
        sockets = self.getPossibleSockets()
        return [
            (socket.identifier, socket.identifier, "")
            for socket in sockets
            if socket.bl_idname in allowedSocketTypes.keys()
        ]

    def getPossibleSockets(self):
        node = self.getSelectedNode()
        identifiers = []
        if node is not None:
            identifiers.extend(
                socket
                for socket in node.inputs
                if socket.bl_idname in allowedSocketTypes.keys()
            )
        return identifiers

    material: PointerProperty(type = Material, update = AnimationNode.refresh)
    nodeName: StringProperty(update = AnimationNode.refresh)
    socketIdentifier: EnumProperty(name = "Socket", items = cacheEnumItems(getPossibleSocketItems),
        update = AnimationNode.refresh)

    def create(self):
        socket = self.getSelectedSocket()
        if socket is not None:
            data = socket.default_value
            self.newInput(allowedSocketTypes[socket.bl_idname], "Data", "data")
            self.inputs["Data"].setProperty(data)

    def draw(self, layout):
        layout.prop(self, "material", text = "")
        if self.material is None: return

        nodeTree = self.material.node_tree
        if nodeTree is None: return

        layout.prop_search(self, "nodeName", nodeTree, "nodes", text = "", icon = "NODE")
        node = self.material.node_tree.nodes.get(self.nodeName)
        if node is None: return

        if self.hasPossibleInputs(node):
            layout.prop(self, "socketIdentifier", text = "")
        else:
            layout.label(text = "No Animatable Inputs", icon = "INFO")

    def hasPossibleInputs(self, node):
        keys = allowedSocketTypes.keys()
        return any(socket.bl_idname in keys for socket in node.inputs)

    def getExecutionCode(self, required):
        inputSocket = self.inputs.get("Data")
        if inputSocket is None: return

        yield "socket = self.getSelectedSocket()"
        yield "if socket is not None:"

        if inputSocket.dataType in ("Float", "Vector"):
            yield "    if socket.default_value != data:"
        elif inputSocket.dataType == "Color":
            yield "    if tuple(socket.default_value) != tuple(data):"

        yield "        socket.default_value = data"

    def getBakeCode(self):
        yield "socket = self.getSelectedSocket()"
        yield "if socket is not None:"
        yield "    socket.keyframe_insert('default_value')"

    def edit(self):
        inputSocket = self.inputs.get("Data")
        if inputSocket is None: return

        if inputSocket.isLinked:
            originIdName = inputSocket.dataOrigin.bl_idname
            possibleIdentifiers = self.getInputIdentifiersFromSocketType(originIdName)
            if inputSocket.bl_idname != originIdName and len(possibleIdentifiers) > 0:
                self.socketIdentifier = possibleIdentifiers[0]

    def getInputIdentifiersFromSocketType(self, searchType):
        sockets = self.getPossibleSockets()
        return [
            socket.identifier
            for socket in sockets
            if allowedSocketTypes[socket.bl_idname] == searchType
        ]

    def getSelectedNode(self):
        if self.material is None: return None

        nodeTree = self.material.node_tree
        if nodeTree is None: return

        return nodeTree.nodes.get(self.nodeName)

    def getSelectedSocket(self):
        node = self.getSelectedNode()
        if node is not None:
            return self.getInputSocketWithIdentifier(node, self.socketIdentifier)
        return None

    def getInputSocketWithIdentifier(self, node, identifier):
        return next(
            (socket for socket in node.inputs if socket.identifier == identifier),
            None,
        )
