from .. sockets.info import getCopyFunction

class ANStruct(dict):

    def copyValues(self):
        s = ANStruct()
        for (dataType, name), value in self.items():
            s[(dataType, name)] = getCopyFunction(dataType)(value)
        return s

    def findDataTypesWithName(self, name):
        return [dataType for dataType, _name in self.keys() if name == _name]

    def findNamesWithDataType(self, dataType):
        return [name for _dataType, name in self.keys() if dataType == _dataType]

    def __repr__(self):
        elements = [f"{repr(name)}: {str(value)}" for (_, name), value in self.items()]
        return f'<AN Struct: {", ".join(elements)} >'
