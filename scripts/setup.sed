[Version]
Class=IEXPRESS
SEDVersion=3

[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=0
HideExtractAnimation=1
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt="OrgMind v2.1 Setup"
DisplayLicense=
FinishMessage="OrgMind has been installed. Double-click the desktop shortcut to start."
TargetName=%TEMP%\OrgMind-Setup-2.1.0.exe
FriendlyName=OrgMind v2.1
AppLaunched=
PostInstallCmd=
AdminQuietInstCmd=
UserQuietInstCmd=
SourceFiles=..\dist\OrgMind\*.*

[SourceFiles]
SourceFiles0=..\dist\OrgMind\
SourceFiles1=..\dist\OrgMind\_internal\

[SourceFiles0]
%FILE0%=

[SourceFiles1]
%FILE1%=
