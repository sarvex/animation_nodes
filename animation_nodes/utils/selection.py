import bpy

sortedSelectionNames = []

def getSortedSelectedObjects():
    return [bpy.data.objects.get(name) for name in getSortedSelectedObjectNames()]

def getSortedSelectedObjectNames():
    return sortedSelectionNames

def updateSelectionSorting(viewLayer):
    global sortedSelectionNames

    selectedNames = getSelectedObjectNames(viewLayer)

    selectedNamesSet = set(selectedNames)
    newSortedSelection = [
        name for name in sortedSelectionNames if name in selectedNamesSet
    ]
    for name in selectedNames:
        if name not in newSortedSelection:
            newSortedSelection.append(name)

    sortedSelectionNames = newSortedSelection

def getSelectedObjectNames(viewLayer):
    return [obj.name for obj in viewLayer.objects if obj.select_get(view_layer = viewLayer)]

def getSelectedObjects(viewLayer):
    return [obj for obj in viewLayer.objects if obj.select_get(view_layer = viewLayer)]

def getActiveObject(viewLayer):
    return viewLayer.objects.active
