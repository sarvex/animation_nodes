from . generic import *

def getSetupInfoList(addonDirectory):
    return [executePythonFile(path) for path in iterSetupInfoPaths(addonDirectory)]

def iterSetupInfoPaths(addonDirectory):
    return iterPathsWithFileName(addonDirectory, "__setup_info.py")
