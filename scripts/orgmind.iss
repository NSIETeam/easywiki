; OrgMind v2.1 — Inno Setup Installer
; Run: iscc scripts\orgmind.iss

[Setup]
AppId={{OrgMind-2.1-2026}}
AppName=OrgMind
AppVersion=2.1.0
AppPublisher=OrgMind Team
AppPublisherURL=https://github.com/orgmind
AppSupportURL=https://github.com/orgmind
AppUpdatesURL=https://github.com/orgmind
DefaultDirName={autopf}\OrgMind
DefaultGroupName=OrgMind
OutputDir=..\dist\installer
OutputBaseFilename=OrgMind-Setup-2.1.0
SetupIconFile=..\orgmind\assets\icon.ico
Compression=lzma2
SolidCompression=yes
UninstallDisplayIcon={app}\OrgMind.exe
UninstallDisplayName=OrgMind v2.1
PrivilegesRequired=admin
WizardStyle=modern

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Files]
Source: "..\dist\OrgMind\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\OrgMind"; Filename: "{app}\OrgMind.exe"; WorkingDir: "{app}"
Name: "{commondesktop}\OrgMind"; Filename: "{app}\OrgMind.exe"; WorkingDir: "{app}"
Name: "{group}\卸载 OrgMind"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\OrgMind.exe"; Description: "{cm:LaunchProgram,OrgMind}"; Flags: nowait postinstall skipifsilent
