import traceback
from .. import tree_info
from .. utils.timing import measureTime
from .. tree_info import getNodesByType, getNetworkByIdentifier
from .. utils.nodes import (
    iterAnimationNodes,
    getAnimationNodeTrees,
    iterNodesInAnimationNodeTrees
)

@measureTime
def updateFile():
    tree_info.updateIfNecessary()

    resetOutdatedInvokeNodes()

    removeUndefinedSockets()

    socketProperties = getSocketProperties()
    links = getLinks()
    removeLinks()

    tree_info.updateIfNecessary()
    for node in iterAnimationNodes():
        try:
            if node.isRefreshable:
                node._refresh()
        except: traceback.print_exc()

    setSocketProperties(socketProperties)
    setLinks(links)

    tree_info.updateIfNecessary()
    for node in iterAnimationNodes():
        node.updateNode()
        tree_info.updateIfNecessary()


# Reset Outdated Invoke Nodes
##############################################

# It is possible that an invoke node have a subprogram identifier of a
# subprogram that no longer exists. So reset those nodes.
def resetOutdatedInvokeNodes():
    for node in getNodesByType("an_InvokeSubprogramNode"):
        if getNetworkByIdentifier(node.subprogramIdentifier) is None:
            node.subprogramIdentifier = ""


# Undefined Sockets
##############################################

def removeUndefinedSockets():
    for node in iterNodesInAnimationNodeTrees():
        if node.bl_idname == "NodeReroute":
            continue

        for socket in node.inputs:
            if not socket.isAnimationNodeSocket:
                removeSocket(node.inputs, socket)
        for socket in node.outputs:
            if not socket.isAnimationNodeSocket:
                removeSocket(node.outputs, socket)

def removeSocket(sockets, socket):
    print("WARNING: socket removed")
    print(f"    Tree: {repr(socket.id_data.name)}")
    print(f"    Node: {repr(socket.node.name)}")
    print(f"    Name: {repr(socket.name)}")
    sockets.remove(socket)


# Socket Data
##############################################

def getSocketProperties():
    socketsByNode = {}
    for node in iterAnimationNodes():
        inputs = {s.identifier : getSocketInfo(s) for s in node.inputs}
        outputs = {s.identifier : getSocketInfo(s) for s in node.outputs}
        socketsByNode[node] = (inputs, outputs)
    return socketsByNode

def setSocketProperties(socketsByNode):
    for node, (inputs, outputs) in socketsByNode.items():
        for socket in node.inputs:
            if socket.identifier in inputs:
                setSocketInfo(socket, inputs[socket.identifier])
        for socket in node.outputs:
            if socket.identifier in outputs:
                setSocketInfo(socket, outputs[socket.identifier])

def getSocketInfo(socket):
    return socket.dataType, socket.getProperty(), socket.hide, socket.isUsed

def setSocketInfo(socket, data):
    socket.hide = data[2]
    socket.isUsed = data[3]
    if socket.dataType == data[0]:
        socket.setProperty(data[1])


# Links
##############################################

def getLinks():
    linksByTree = {}
    for tree in getAnimationNodeTrees():
        links = [
            (
                link.from_node,
                link.from_socket.identifier,
                link.to_node,
                link.to_socket.identifier,
            )
            for link in tree.links
        ]
        linksByTree[tree] = links
    return linksByTree

def removeLinks():
    for tree in getAnimationNodeTrees():
        tree.links.clear()

def setLinks(linksByTree):
    for tree, links in linksByTree.items():
        for fromNode, fromIdentifier, toNode, toIdentifier in links:
            fromSocket = getSocketByIdentifier(fromNode.outputs, fromIdentifier)
            toSocket = getSocketByIdentifier(toNode.inputs, toIdentifier)
            if fromSocket is not None and toSocket is not None:
                tree.links.new(toSocket, fromSocket)
            else:
                print("WARNING: link removed")
                print(f"    Tree: {repr(tree.name)}")
                print(f"    From Socket: {repr(fromNode.name)} -> {repr(fromIdentifier)}")
                print(f"    To Socket: {repr(toNode.name)} -> {repr(toIdentifier)}\n")

def getSocketByIdentifier(sockets, identifier):
    for socket in sockets:
        if socket.identifier == identifier:
            return socket

############
# Versioning
############

def runVersioning():
    runVersioningSceneChanged()

# The "sceneUpdate" property of AutoExecutionProperties was deprecated, its function was identical
# to that of the newly added "always" property. For files where the "always" property is not set,
# that is, files that were saved before this change, we set the value of the "always" property to
# that of the deprecated "sceneUpdate" property. Additionally, since the newly added "sceneChanged"
# property is functionally somewhat similar to the "always" property, we also set its value to that
# of the deprecated "sceneUpdate" property.
def runVersioningSceneChanged():
    for tree in getAnimationNodeTrees():
        if tree.autoExecution.is_property_set("always"): continue
        tree.autoExecution.always = tree.autoExecution.sceneUpdate
        tree.autoExecution.sceneChanged = tree.autoExecution.sceneUpdate
