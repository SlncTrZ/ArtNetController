; Inno Setup Script for DMX Master LTS 1.0.6
; Professional Art-Net Lighting Controller Installer

#define MyAppName "DMX Master LTS"
#define MyAppVersion "1.0.6"
#define MyAppPublisher "Cong Dinh Truong"
#define MyAppURL "https://github.com/truongcongdinh97/DMX-Master"
#define MyAppExeName "DMXMaster-LTS-1.0.6.exe"
#define MyAppDescription "Professional Art-Net Lighting Controller with Enhanced DMX View"

[Setup]
; Application info
AppId={{DMX-MASTER-LTS-106-2025-11-06}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (C) 2025 {#MyAppPublisher}

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes

; Output
OutputDir=installer_output
OutputBaseFilename=DMX-Master-LTS-1.0.6-Setup
SetupIconFile=assets\DMXMaster.ico
Compression=lzma2/max
SolidCompression=yes

; Privileges
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; UI
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
; WizardImageFile=assets\installer\wizard-image.bmp
; WizardSmallImageFile=assets\installer\wizard-small.bmp

; Version info
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppDescription} Installer
VersionInfoCopyright=Copyright (C) 2025 {#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

; License and info
LicenseFile=LICENSE.txt
; InfoAfterFile=INSTALLATION_INFO.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable
Source: "dist\DMXMaster-LTS-1.0.6.exe"; DestDir: "{app}"; Flags: ignoreversion

; Default shows and data (for copying to AppData on first run)
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

; Assets (icons, images)
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs

; Requirements and source (optional - for advanced users)
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppDescription}"
Name: "{group}\{#MyAppName} Documentation"; Filename: "{app}\docs\INDEX.md"; Comment: "User Guide and Documentation"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop icon (if selected)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppDescription}"; Tasks: desktopicon

; Quick Launch icon (if selected)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Option to launch after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; Option to view documentation
Filename: "{app}\README.md"; Description: "View README and Getting Started Guide"; Flags: postinstall skipifsilent shellexec unchecked

[UninstallDelete]
; Clean up application files only (user data is in AppData)
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\assets"
Type: filesandordirs; Name: "{app}\docs"

[Code]
{ Custom installation logic }

// Check Windows version
function InitializeSetup(): Boolean;
begin
  // Require Windows 10 or later
  if not (GetWindowsVersion >= $0A000000) then
  begin
    MsgBox('DMX Master LTS requires Windows 10 or later.', mbError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;

// Post-installation tasks
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // No longer need to create directories here
    // Application creates all data directories in AppData on first run
  end;
end;

// Pre-uninstall cleanup
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    // User data (shows, recordings, config, logs) are in AppData
    // Show message about how to clean AppData if needed
    MsgBox('DMX Master has been uninstalled.' + #13#10 + #13#10 +
           'Your shows, recordings, and settings are preserved in:' + #13#10 +
           '%LOCALAPPDATA%\DMX Master LTS' + #13#10 + #13#10 +
           'To completely remove all data, manually delete that folder.', 
           mbInformation, MB_OK);
  end;
end;
