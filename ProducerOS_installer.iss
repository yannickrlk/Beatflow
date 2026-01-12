; ProducerOS Installer Script for Inno Setup
; Download Inno Setup: https://jrsoftware.org/isinfo.php

#define MyAppName "ProducerOS"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "ProducerOS"
#define MyAppExeName "ProducerOS.exe"
#define MyAppURL "https://produceros.app"
#define MyAppSupportURL "https://produceros.app/support"

[Setup]
AppId={{7DE1E839-77D7-4321-9D1B-C8C3CE7C74A3}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppSupportURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright 2026 ProducerOS
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=legal\EULA.txt
InfoBeforeFile=legal\PRIVACY.md
OutputDir=installer
OutputBaseFilename=ProducerOS_Setup_v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
; Uncomment when icon is ready:
; SetupIconFile=assets\icon.ico
; UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\ProducerOS\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\ProducerOS\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; Include legal files
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "NOTICE"; DestDir: "{app}"; Flags: ignoreversion
Source: "legal\PRIVACY.md"; DestDir: "{app}\legal"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
