Set shell = CreateObject("WScript.Shell")
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
pythonw = scriptDir & "\venv\Scripts\pythonw.exe"
target = scriptDir & "\app\main.py"
shell.Run """" & pythonw & """ """ & target & """", 0, False
