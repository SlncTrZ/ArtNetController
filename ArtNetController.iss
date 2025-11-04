; Inno Setup Script for ArtNetController V2.0
; Automatically generated installer script

#define MyAppName "ArtNetController"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "DMX Master"
#define MyAppURL "https://github.com/truongcongdinh97/DMX-Master"
#define MyAppExeName "ArtNetController.exe"

[Setup]
; Application info
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output
OutputDir=.
OutputBaseFilename=ArtNetController-{#MyAppVersion}-Setup
SetupIconFile=assets\DMXMaster.ico
Compression=lzma2/max
SolidCompression=yes

; Privileges
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; UI
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

; Version info
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Installer
VersionInfoCopyright=Copyright (C) 2025 {#MyAppPublisher}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable and all dependencies
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Config file template (don't overwrite if exists)
; Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop icon (if selected)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch icon (if selected)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Option to launch after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up user data on uninstall (optional - commented out to preserve user data)
; Type: filesandordirs; Name: "{app}\logs"
; Type: filesandordirs; Name: "{app}\config_backups"
; Type: filesandordirs; Name: "{app}\shows"
; Type: files; Name: "{app}\config.json"

[Code]
{ Custom Pascal Script for advanced features }

// Check if .NET Framework is installed (if needed)
// function IsDotNetInstalled: Boolean;
// begin
//   Result := RegKeyExists(HKLM, 'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full');
// end;

// Custom page or checks can be added here
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Post-installation tasks
    // Example: Create shortcuts, register protocols, etc.
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Post-uninstallation cleanup
    // Example: Remove registry entries, etc.
  end;
end;
