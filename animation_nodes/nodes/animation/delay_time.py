import bpy
from . c_utils import executeSubtract_A_B
from ... base_types import AnimationNode, VectorizedSocket
from ... data_structures import VirtualDoubleList, DoubleList

class DelayTimeNode(AnimationNode, bpy.types.Node):
    bl_idname = "an_DelayTimeNode"
    bl_label = "Delay Time"
    dynamicLabelType = "HIDDEN_ONLY"

    useListA: VectorizedSocket.newProperty()
    useListB: VectorizedSocket.newProperty()
    

    def create(self):
        self.newInput(VectorizedSocket("Float", "useListA",
            ("Time", "time"), ("Times", "times")))
        self.newInput(VectorizedSocket("Float", "useListB",
            ("Delay", "delay", dict(value = 10)),
            ("Delays", "delays")))
        self.newOutput(VectorizedSocket("Float",
            ["useListA", "useListB"],
            ("Time", "outTime"), ("Times", "outTimes")))

    def drawLabel(self):
        if self.useListB: return "Delay Time"
        delaySocket = self.inputs["Delay"]
        if not delaySocket.isUnlinked:
            return "Delay Time"
        value = delaySocket.value
        return (
            f"Delay {int(value)} Frames"
            if value == int(value)
            else f"Delay {str(round(value, 2))} Frames"
        )

    def getExecutionCode(self, required):
        if self.useListA or self.useListB:
            args = ", ".join(socket.identifier for socket in self.inputs)
            return f"outTimes = self.executeList({args})"
        else:
            return "outTime = time - delay"

    def executeList(self, time, delay):
        virtualTimes, virtualDelays = VirtualDoubleList.createMultiple((time, 0), (delay, 0))
        amount = VirtualDoubleList.getMaxRealLength(virtualTimes, virtualDelays)

        return executeSubtract_A_B(virtualTimes, virtualDelays, amount)

