import bpy
from collections import defaultdict
from .. utils.enum_items import enumItemsFromList
from .. utils.nodes import iterSubclassesWithAttribute
from . implicit_conversion import iterTypesThatCanConvertTo

class SocketInfo:
    def __init__(self):
        self.reset()

    def reset(self):
        self.idNames = set()
        self.dataTypes = set()

        self.classByType = {}
        self.typeConversion = {}
        self.allowedInputDataTypes = {}
        self.allowedTargetDataTypes = defaultdict(set)

        self.baseIdName = {}
        self.listIdName = {}
        self.baseDataType = {}
        self.listDataType = {}

        self.baseDataTypes = set()
        self.listDataTypes = set()
        self.drawableDataTypes = set()

        self.copyFunctionByType = {}

    def update(self, socketClasses):
        self.reset()

        # create lookup tables first
        for socket in socketClasses:
            self.insertSocket(socket)

        # then insert the socket connections
        for socket in socketClasses:
            if hasattr(socket, "baseType"):
                self.insertSocketConnection(socket.baseType.dataType, socket.dataType)

        # insert allowed input data types
        for socket in socketClasses:
            inputTypes = self.getAllowedInputDataTypes(socket)

            self.allowedInputDataTypes[socket.dataType] = inputTypes
            self.allowedInputDataTypes[socket.bl_idname] = inputTypes

            for inputType in inputTypes:
                self.allowedTargetDataTypes[inputType].add(socket.dataType)
                self.allowedTargetDataTypes[self.typeConversion[inputType]].add(socket.dataType)

    def insertSocket(self, socketClass):
        idName = socketClass.bl_idname
        dataType = socketClass.dataType

        self.idNames.add(idName)
        self.dataTypes.add(dataType)

        self.classByType[idName] = socketClass
        self.classByType[dataType] = socketClass

        self.typeConversion[idName] = dataType
        self.typeConversion[dataType] = idName

        if socketClass.isCopyable():
            copyFunction = eval(f"lambda value: {socketClass.getCopyExpression()}")
        else:
            copyFunction = lambda value: value

        self.copyFunctionByType[idName] = copyFunction
        self.copyFunctionByType[dataType] = copyFunction

        if socketClass.hasProperty():
            self.drawableDataTypes.add(socketClass.dataType)

    def insertSocketConnection(self, baseDataType, listDataType):
        baseIdName = self.typeConversion[baseDataType]
        listIdName = self.typeConversion[listDataType]

        self.baseIdName[listIdName] = baseIdName
        self.baseIdName[listDataType] = baseIdName
        self.listIdName[baseIdName] = listIdName
        self.listIdName[baseDataType] = listIdName

        self.baseDataType[listIdName] = baseDataType
        self.baseDataType[listDataType] = baseDataType
        self.listDataType[baseIdName] = listDataType
        self.listDataType[baseDataType] = listDataType

        self.baseDataTypes.add(baseDataType)
        self.listDataTypes.add(listDataType)

    def getAllowedInputDataTypes(self, socket):
        if hasattr(socket, "allowedInputTypes"):
            if "All" in socket.allowedInputTypes:
                inputTypes = self.dataTypes
            else:
                inputTypes = set(socket.allowedInputTypes)
        else:
            inputTypes = {socket.dataType}

        inputTypes.update(iterTypesThatCanConvertTo(socket.dataType))
        return inputTypes


_socketInfo = SocketInfo()

def updateSocketInfo():
    socketClasses = getSocketClasses()
    _socketInfo.update(socketClasses)

def getSocketClasses():
    from .. base_types import AnimationNodeSocket
    return list(iterSubclassesWithAttribute(AnimationNodeSocket, "bl_idname"))


# Check if list or base socket exists
def isList(input):
    return input in _socketInfo.baseDataType.keys()

def isBase(input):
    return input in _socketInfo.listDataType.keys()

# to Base
def toBaseIdName(input):
    return _socketInfo.baseIdName[input]

def toBaseDataType(input):
    return _socketInfo.baseDataType[input]

# to List
def toListIdName(input):
    return _socketInfo.listIdName[input]

def toListDataType(input):
    return _socketInfo.listDataType[input]

# Data Type <-> Id Name
def toIdName(input):
    return input if isIdName(input) else _socketInfo.typeConversion[input]

def toDataType(input):
    return _socketInfo.typeConversion[input] if isIdName(input) else input

def isIdName(name):
    return name in _socketInfo.idNames


def isComparable(input):
    return _socketInfo.classByType[input].comparable

def isCopyable(input):
    return _socketInfo.classByType[input].isCopyable()

def getCopyExpression(input):
    return _socketInfo.classByType[input].getCopyExpression()

def getCopyFunction(input):
    return _socketInfo.copyFunctionByType[input]

def hasAllowedInputDataTypes(input):
    return len(_socketInfo.allowedInputDataTypes[input]) > 0

def getAllowedInputDataTypes(input):
    return _socketInfo.allowedInputDataTypes[input]

def getAllowedTargetDataTypes(input):
    return _socketInfo.allowedTargetDataTypes[input]

def getSocketClass(input):
    return _socketInfo.classByType[input]


def getDefaultValue(input):
    return _socketInfo.classByType[input].getDefaultValue()

def getBaseDefaultValue(input):
    return _socketInfo.classByType[input].baseType.getDefaultValue()


def getListDataTypeItems():
    return enumItemsFromList(getListDataTypes())

def getBaseDataTypeItems():
    return enumItemsFromList(getBaseDataTypes())

def getDrawableDataTypeItems():
    return enumItemsFromList(getDrawableDataTypes())

def getDataTypeItems(skipInternalTypes = False):
    return enumItemsFromList(getDataTypes(skipInternalTypes))

def getListDataTypes():
    return list(_socketInfo.listDataTypes)

def getBaseDataTypes():
    return list(_socketInfo.baseDataTypes)

def getDrawableDataTypes():
    return list(_socketInfo.drawableDataTypes)

def getDataTypes(skipInternalTypes = False):
    if not skipInternalTypes:
        return list(_socketInfo.dataTypes)
    internalTypes = {"Node Control"}
    return [dataType for dataType in _socketInfo.dataTypes if dataType not in internalTypes]
