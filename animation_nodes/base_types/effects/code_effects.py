from ... utils.names import replaceVariableName
from ... utils.attributes import hasEvaluableRepr

class CodeEffect:
    def apply(self, node, code, required):
        return code

    def iterIndented(self, code):
        yield from (f"    {line}" for line in code.splitlines())

class DefaultBaseElement:
    pass

class VectorizeCodeEffect(CodeEffect):
    def __init__(self):
        self.baseInputNames = []
        self.listInputNames = []
        self.newBaseInputNames = []
        self.inputIndices = []
        self.allowInputListExtension = []
        self.defaultInputElements = []

        self.baseOutputNames = []
        self.listOutputNames = []
        self.newBaseOutputNames = []
        self.outputIndices = []

    def input(self, baseName, listName, index, allowListExtension = True, defaultElement = DefaultBaseElement):
        self.baseInputNames.append(baseName)
        self.listInputNames.append(listName)
        self.newBaseInputNames.append(self.rename(baseName))
        self.inputIndices.append(index)
        self.allowInputListExtension.append(allowListExtension)

        if defaultElement is not DefaultBaseElement and not hasEvaluableRepr(
            defaultElement
        ):
            raise Exception(
                f"This type does not allow 'eval(repr(value))': {str(defaultElement)}"
            )
        self.defaultInputElements.append(defaultElement)

    def output(self, baseName, listName, index):
        self.baseOutputNames.append(baseName)
        self.listOutputNames.append(listName)
        self.newBaseOutputNames.append(self.rename(baseName))
        self.outputIndices.append(index)

    def rename(self, name):
        return f"_base_{name}"

    def apply(self, node, code, required):
        if len(self.baseInputNames) == 0:
            yield code
            return

        iteratorName = "vectorizeIterator"
        yield from self.iterOutputListCreationLines(node)
        yield from self.iterIteratorCreationLines(iteratorName)
        yield self.getLoopStartLine(iteratorName)
        yield from self.iterIndented(self.renameVariables(code))
        yield from self.iterAppendToOutputListLines(node)
        yield "    pass"

    def iterOutputListCreationLines(self, node):
        for name, index in zip(self.listOutputNames, self.outputIndices):
            socket = node.outputs[index]
            if socket.isLinked and name not in self.listInputNames:
                yield f"{name} = self.outputs[{index}].getDefaultValue()"

    def iterIteratorCreationLines(self, iteratorName):
        if len(self.listInputNames) == 1:
            yield f"{iteratorName} = {self.listInputNames[0]}"
        else:
            amountName = "iterations"
            yield from self.iterGetIterationAmountLines(amountName)
            for i, (name, allowExtension) in enumerate(zip(self.listInputNames,
                                                           self.allowInputListExtension)):
                iterName = f"{name}_iter"
                if allowExtension:
                    yield from self.iterCreateInputListIteratorLines(i, name, iterName, amountName)
                else:
                    yield "{0}_iter = {0}".format(name)

            iterators = ", ".join(f"{name}_iter" for name in self.listInputNames)
            yield f"{iteratorName} = zip({iterators})"

    def iterGetIterationAmountLines(self, amountName):
        noExtAmount = self.allowInputListExtension.count(False)
        if noExtAmount == 0:
            lengths = [f"len({name})" for name in self.listInputNames]
            yield f'{amountName} = max({", ".join(lengths)})'
        elif noExtAmount == 1:
            yield f"{amountName} = len({self.listInputNames[self.allowInputListExtension.index(False)]})"
        else:
            lengths = [
                f"len({name})"
                for name, allowExtension in zip(
                    self.listInputNames, self.allowInputListExtension
                )
                if not allowExtension
            ]
            yield f'{amountName} = min({", ".join(lengths)})'

    def iterCreateInputListIteratorLines(self, i, name, iterName, amountName):
        default = self.defaultInputElements[i]
        index = self.inputIndices[i]
        if default is DefaultBaseElement:
            _default = f"self.inputs[{index}].baseType.getDefaultValue()"
        else:
            defaultRepr = repr(default)
            _default = f"self.inputs[{index}].baseType.correctValue({defaultRepr})[0]"

        yield f"if len({name}) >= {amountName}:"
        yield f"    {iterName} = {name}"
        yield f"elif len({name}) == 0:"
        yield f"    {iterName} = itertools.cycle([{_default}])"
        yield f"elif len({name}) < {amountName}:"
        yield f"    {iterName} = itertools.cycle({name})"

    def getLoopStartLine(self, iteratorName):
        return f'for {", ".join(self.newBaseInputNames)} in {iteratorName}:'

    def iterAppendToOutputListLines(self, node):
        for baseName, listName, index in zip(self.newBaseOutputNames, self.listOutputNames, self.outputIndices):
            socket = node.outputs[index]
            if socket.isLinked and listName not in self.listInputNames:
                yield f"    {listName}.append({baseName})"

    def renameVariables(self, code):
        for oldName, newName in zip(self.baseInputNames + self.baseOutputNames,
                                    self.newBaseInputNames + self.newBaseOutputNames):
            code = replaceVariableName(code, oldName, newName)
        return code


class PrependCodeEffect(CodeEffect):
    def __init__(self, codeToPrepend):
        self.codeToPrepend = codeToPrepend

    def apply(self, node, code, required):
        yield self.codeToPrepend
        yield code


class ReturnDefaultsOnExceptionCodeEffect(CodeEffect):
    def __init__(self, exceptionString):
        self.exceptionString = exceptionString

    def apply(self, node, code, required):
        yield "try:"
        yield from self.iterIndented(code)
        yield "    pass"
        yield f"except {self.exceptionString}:"
        outputVariables = node.getOutputSocketVariables()
        for i, s in enumerate(node.outputs):
            if s.identifier in required:
                if hasattr(s, "getDefaultValueCode"):
                    yield f"    {outputVariables[s.identifier]} = {s.getDefaultValueCode()}"
                else:
                    yield f"    {outputVariables[s.identifier]} = self.outputs[{i}].getDefaultValue()"
        yield "    pass"
