Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
appDir = fso.GetParentFolderName(WScript.ScriptFullName)
exePath = appDir & "\dist\OrgMind-Demo.exe"
WshShell.Run """" & exePath & """", 0, False
Dim http, i
For i = 1 To 60
    WScript.Sleep 500
    On Error Resume Next
    Set http = CreateObject("MSXML2.ServerXMLHTTP")
    http.open "GET", "http://localhost:8080/health", False
    http.send
    If http.status = 200 Then
        WshShell.Run "explorer http://localhost:8080", 1, False
        WScript.Quit 0
    End If
    On Error Goto 0
Next
