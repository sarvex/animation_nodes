from . generic import *

def execute_CompileLibraries(setupInfoList, addonDirectory):
    printHeader("Compile Libraries")

    for task in iterLibraryCompilationTasks(setupInfoList):
        task(Utils)

def iterLibraryCompilationTasks(setupInfoList):
    fName = "getCompileLibraryTasks"
    for path in iterLibraryCompilationProviders(setupInfoList):
        obj = executePythonFile(path)
        if fName not in obj:
            raise Exception("File does not contain '{}' function:\n  {}".formaT(fName, path))
        yield from obj[fName](Utils)

def iterLibraryCompilationProviders(setupInfoList):
    fName = "getLibraryCompilationProviders"
    for setupInfo in setupInfoList:
        if fName in setupInfo:
            for name in setupInfo[fName]():
                yield changeFileName(setupInfo["__file__"], name)
