from . generic import *

def execute_Cythonize(setupInfoList, addonDirectory, configs):
    printHeader("Run Cythonize")
    tasks = getCythonizeTasks(addonDirectory, configs)
    for i, task in enumerate(tasks, 1):
        print(f"{i}/{len(tasks)}:")
        task.execute()

def getCythonizeTasks(addonDirectory, configs):
    includePaths = configs.get("Cython Include Paths", [])
    includePaths.append(".")

    return [
        CythonizeTask(path, includePaths)
        for path in iterCythonFilePaths(addonDirectory)
    ]

def iterCythonFilePaths(addonDirectory):
    yield from iterPathsWithExtension(addonDirectory, ".pyx")

class CythonizeTask:
    def __init__(self, path, includePaths):
        self.path = path
        self.includePaths = includePaths

    def execute(self):
        from Cython.Build import cythonize
        cythonize(self.path, include_path = self.includePaths, compiler_directives = {"language_level" : "3"})
