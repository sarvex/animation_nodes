from .. utils.code import isCodeValid, getSyntaxError, containsStarImport
from . compile_scripts import compileScript
from .. problems import ExecutionUnitNotSetup
from . code_generator import getSocketValueExpression, iterSetupCodeLines, getInitialVariables

userCodeStartComment = "# User Code"

class ScriptExecutionUnit:
    def __init__(self, network, nodeByID):
        self.network = network
        self.setupScript = ""
        self.setupCodeObject = None
        self.executionData = {}

        self.scriptUpdated(nodeByID)

    def scriptUpdated(self, nodeByID = None):
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
        node = self.network.getScriptNode(nodeByID)
        userCode = node.executionCode

        variables = getInitialVariables([node])

        finalCode = []
        finalCode.extend(iterSetupCodeLines([node], variables))
        finalCode.append(self.getFunctionHeader(node))

        if containsStarImport(userCode):
            finalCode.append(
                f"    {node.identifier}.errorMessage = 'Star import is not allowed'"
            )
        elif isCodeValid(userCode):
            finalCode.extend(indent(self.getFunctionBodyLines(node, userCode)))

            # used to show the correct line numbers to the user
            lineNumber = findFirstLineIndexWithContent(finalCode, userCodeStartComment) + 1
            finalCode.append(f"USER_CODE_START_LINE = {lineNumber}")
        else:
            error = getSyntaxError(userCode)
            finalCode.extend(
                (
                    f"    {node.identifier}.errorMessage = 'Line: {error.lineno} - Invalid Syntax'",
                    f"    {self.getDefaultReturnStatement(node)}",
                )
            )
        self.setupScript = "\n".join(finalCode)

    def getFunctionBodyLines(self, node, userCode):
        lines = ["\n", userCodeStartComment]
        lines.extend(userCode.split("\n"))
        lines.append("\n")
        if node.initializeMissingOutputs:
            lines.extend(self.iterInitializeMissingOutputsLines(node))
        if node.correctOutputTypes:
            lines.extend(self.iterTypeCorrectionLines(node))
        lines.append(self.getReturnStatement(node))

        if node.debugMode:
            return list(self.iterDebugModeFunctionBody(lines, node))
        else:
            return lines

    def iterDebugModeFunctionBody(self, lines, node):
        yield "try:"
        yield f"    {node.identifier}.errorMessage = ''"
        yield from indent(lines)
        yield "except Exception as e:"
        yield "    __exceptionType, __exception, __tb = sys.exc_info()"
        yield "    __lineNumber = __tb.tb_lineno - USER_CODE_START_LINE"
        yield "    {}.errorMessage = 'Line: {{}} - {{}} ({{}})'.format(__lineNumber, __exception, type(e).__name__)".format(node.identifier)
        yield f"    {self.getDefaultReturnStatement(node)}"

    def getFunctionHeader(self, node):
        inputNames = [socket.text for socket in node.inputs[:-1]]
        parameterList = ", ".join(inputNames)
        return f"def main({parameterList}):"

    def iterInitializeMissingOutputsLines(self, node):
        yield ""
        yield "# initialize missing outputs"
        yield "localVariables = locals()"
        for i, socket in enumerate(node.outputs[:-1]):
            variableName = socket.text
            yield f"__socket = {node.identifier}.outputs[{i}]"
            yield f"__socket['variableInitialized'] = {repr(variableName)} in localVariables"
            yield "if not __socket['variableInitialized']:"
            yield f"    {variableName} = __socket.getDefaultValue()"

    def iterTypeCorrectionLines(self, node):
        yield ""
        yield "# correct output types"
        for i, socket in enumerate(node.outputs[:-1]):
            variableName = socket.text
            yield f"__socket = {node.identifier}.outputs[{i}]"
            yield "{0}, __socket['correctionType'] = __socket.correctValue({0})".format(variableName)

    def getReturnStatement(self, node):
        outputNames = [socket.text for socket in node.outputs[:-1]]
        returnList = ", ".join(outputNames)
        return f"return {returnList}"

    def getDefaultReturnStatement(self, node):
        outputSockets = node.outputs[:-1]
        outputExpressions = [getSocketValueExpression(socket, node) for socket in outputSockets]
        return "return " + ", ".join(outputExpressions)

    def compileScript(self):
        self.setupCodeObject = compileScript(
            self.setupScript, name=f"script: {repr(self.network.name)}"
        )

    def raiseNotSetupException(self):
        raise ExecutionUnitNotSetup()

def indent(lines, amount = 1):
    return (" " * (4 * amount) + line for line in lines) # returns a generator

def findFirstLineIndexWithContent(lines, content):
    return next(
        (i for i, line in enumerate(lines, start=1) if content in line), 0
    )
