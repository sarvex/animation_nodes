from .. sockets.info import toIdName
from .. tree_info import getNodesByType
from . compile_scripts import compileScript
from .. problems import ExecutionUnitNotSetup
from . code_generator import (getInitialVariables,
                              iterSetupCodeLines,
                              getCopyExpression,
                              iterNodeCommentLines,
                              getGlobalizeStatement,
                              getLoadSocketValueLine,
                              iterInputConversionLines,
                              linkOutputSocketsToTargets,
                              getFunction_IterNodeExecutionLines)

class LoopExecutionUnit:
    def __init__(self, network, nodeByID):
        self.network = network
        self.setupScript = ""
        self.setupCodeObject = None
        self.executionData = {}

        self.generateScript(nodeByID)
        self.compileScript()
        self.execute = self.raiseNotSetupException


    def setup(self):
        self.executionData = {}
        exec(self.setupCodeObject, self.executionData, self.executionData)
        self.execute = self.executionData["main"]

    def insertSubprogramFunctions(self, data):
        self.executionData.update(data)

    def finish(self):
        self.executionData.clear()
        self.execute = self.raiseNotSetupException


    def getCodes(self):
        return [self.setupScript]



    def generateScript(self, nodeByID):
        try: nodes = self.network.getSortedAnimationNodes(nodeByID)
        except: return

        variables = getInitialVariables(nodes)
        self.setupScript = "\n".join(self.iterSetupScriptLines(nodes, variables, nodeByID))

    def iterSetupScriptLines(self, nodes, variables, nodeByID):
        inputNode = self.network.getLoopInputNode(nodeByID)

        yield from iterSetupCodeLines(nodes, variables)
        yield "\n\n"

        if inputNode.iterateThroughLists:
            yield from self.iter_IteratorLength(inputNode, nodes, variables, nodeByID)
        else:
            yield from self.iter_IterationsAmount(inputNode, nodes, variables, nodeByID)


    def iter_IterationsAmount(self, inputNode, nodes, variables, nodeByID):
        yield self.get_IterationsAmount_Header(inputNode, variables)
        yield f"    {getGlobalizeStatement(nodes, variables)}"
        yield from iterIndented(self.iter_InitializeGeneratorsLines(inputNode, variables, nodeByID))
        yield from iterIndented(self.iter_InitializeParametersLines(inputNode, variables))
        yield from iterIndented(self.iter_IterationsAmount_PrepareLoop(inputNode, variables))
        yield from iterIndented(self.iter_LoopBody(inputNode, nodes, variables, nodeByID), amount = 2)
        yield from iterIndented(self.iter_UpdateLoopViewerNodes(nodeByID))
        yield f"    {self.get_ReturnStatement(inputNode, variables, nodeByID)}"

    def get_IterationsAmount_Header(self, inputNode, variables):
        variables[inputNode.iterationsSocket] = "loop_iterations"
        parameterNames = ["loop_iterations"]
        for i, socket in enumerate(inputNode.getParameterSockets()):
            if socket.loop.useAsInput:
                name = f"loop_parameter_{str(i)}"
                variables[socket] = name
                parameterNames.append(name)

        return f'def main({", ".join(parameterNames)}):'

    def iter_IterationsAmount_PrepareLoop(self, inputNode, variables):
        variables[inputNode.indexSocket] = "current_loop_index"
        yield "for current_loop_index in range(loop_iterations):"


    def iter_IteratorLength(self, inputNode, nodes, variables, nodeByID):
        yield self.get_IteratorLength_Header(inputNode, variables)
        yield f"    {getGlobalizeStatement(nodes, variables)}"
        yield from iterIndented(self.iter_InitializeGeneratorsLines(inputNode, variables, nodeByID))
        yield from iterIndented(self.iter_InitializeParametersLines(inputNode, variables))
        yield from iterIndented(self.iter_IteratorLength_PrepareLoopLines(inputNode, variables))
        yield from iterIndented(self.iter_LoopBody(inputNode, nodes, variables, nodeByID), amount = 2)
        yield from iterIndented(self.iter_UpdateLoopViewerNodes(nodeByID))
        yield f"    {self.get_ReturnStatement(inputNode, variables, nodeByID)}"

    def get_IteratorLength_Header(self, inputNode, variables):
        parameterNames = []
        for i, socket in enumerate(inputNode.getIteratorSockets()):
            name = f"loop_iterator_{str(i)}"
            parameterNames.append(name)
        for i, socket in enumerate(inputNode.getParameterSockets()):
            if socket.loop.useAsInput:
                name = f"loop_parameter_{str(i)}"
                variables[socket] = name
                parameterNames.append(name)

        return f'def main({", ".join(parameterNames)}):'

    def iter_IteratorLength_PrepareLoopLines(self, inputNode, variables):
        iterators = inputNode.getIteratorSockets()
        iteratorNames = [f"loop_iterator_{str(i)}" for i in range(len(iterators))]

        if inputNode.iterationsSocket.isLinked:
            yield f'zipped_iterators = list(zip({", ".join(iteratorNames)}))'
            yield "loop_iterations = len(zipped_iterators)"
        else:
            # loop_iterations doesn't have to be calculated
            #  -> no need to make a list of the zip object
            yield f'zipped_iterators = zip({", ".join(iteratorNames)})'

        names = []
        for i, socket in enumerate(iterators):
            name = f"loop_iterator_element_{str(i)}"
            variables[socket] = name
            names.append(name)

        yield f'for current_loop_index, ({", ".join(names)}, ) in enumerate(zipped_iterators):'

        variables[inputNode.indexSocket] = "current_loop_index"
        variables[inputNode.iterationsSocket] = "loop_iterations"

    def iter_UpdateLoopViewerNodes(self, nodeByID):
        for node in getNodesByType("an_LoopViewerNode", nodeByID):
            if self.network == node.network:
                yield f"{node.identifier}.updateTextBlock()"
                yield f"{node.identifier}.clearOutputLines()"

    def iter_InitializeGeneratorsLines(self, inputNode, variables, nodeByID):
        for i, node in enumerate(inputNode.getSortedGeneratorNodes(nodeByID)):
            name = f"loop_generator_output_{str(i)}"
            variables[node] = name
            yield f"{name} = AN.sockets.info.getDefaultValue({repr(node.listDataType)})"
            yield "{0}_{1} = {1}.{0}".format(node.generatorType, name)

    def iter_InitializeParametersLines(self, inputNode, variables):
        for socket in inputNode.getParameterSockets():
            if not socket.loop.useAsInput:
                yield getLoadSocketValueLine(socket, inputNode, variables)


    def iter_LoopBody(self, inputNode, nodes, variables, nodeByID):
        yield from linkOutputSocketsToTargets(inputNode, variables, nodeByID)

        iterNodeExecutionLines = getFunction_IterNodeExecutionLines()
        ignoreNodes = {"an_LoopInputNode", "an_LoopGeneratorOutputNode", "an_ReassignLoopParameterNode", "an_LoopBreakNode"}
        for node in nodes:
            if node.bl_idname in ignoreNodes: continue
            yield from iterNodeExecutionLines(node, variables)
            yield from linkOutputSocketsToTargets(node, variables, nodeByID)

        yield from self.iter_LoopBreak(inputNode, variables, nodeByID)
        yield from self.iter_AddToGenerators(inputNode, variables, nodeByID)
        yield from self.iter_ReassignParameters(inputNode, variables, nodeByID)
        yield "pass"

    def iter_LoopBreak(self, inputNode, variables, nodeByID):
        for node in inputNode.getBreakNodes(nodeByID):
            yield f"if not {variables[node.inputs[0]]}: break"

    def iter_AddToGenerators(self, inputNode, variables, nodeByID):
        for node in inputNode.getSortedGeneratorNodes(nodeByID):
            yield from iterNodeCommentLines(node)
            yield f"if {variables[node.conditionSocket]}:"

            socket = node.dataInputSocket
            if socket.isUnlinked and socket.isCopyable(): expression = getCopyExpression(socket, variables)
            else: expression = variables[socket]
            yield f"    {node.generatorType}_{variables[node]}({expression})"

    def iter_ReassignParameters(self, inputNode, variables, nodeByID):
        for node in inputNode.getReassignParameterNodes(nodeByID):
            yield from iterNodeCommentLines(node)
            yield from iterInputConversionLines(node, variables)

            socket = node.inputs[0]
            if socket.isUnlinked and socket.isCopyable(): expression = getCopyExpression(socket, variables)
            else: expression = variables[socket]

            if node.conditionSocket is None: conditionPrefix = ""
            else:else
                conditionPrefix = f"if {variables[node.conditionSocket]}: "

            yield f"{conditionPrefix}{variables[node.linkedParameterSocket]} = {expression}"


    def get_ReturnStatement(self, inputNode, variables, nodeByID):
        names = [
            f"loop_iterator_{str(i)}"
            for i, socket in enumerate(inputNode.getIteratorSockets())
            if socket.loop.useAsOutput
        ]
        names.extend([variables[node] for node in inputNode.getSortedGeneratorNodes(nodeByID)])
        names.extend([variables[socket] for socket in inputNode.getParameterSockets() if socket.loop.useAsOutput])
        return f'return {", ".join(names)}'



    def compileScript(self):
        self.setupCodeObject = compileScript(
            self.setupScript, name=f"group: {repr(self.network.name)}"
        )


    def raiseNotSetupException(self):
        raise ExecutionUnitNotSetup()

def joinLines(lines):
    return "\n".join(lines)

def indent(lines, amount = 1):
    return [" " * (4 * amount) + line for line in lines]

def iterIndented(lines, amount = 1):
    indentation = "    " * amount
    for line in lines:
        yield indentation + line
