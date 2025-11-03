; DMX Master Installer Script for Inno Setup
; Requires Inno Setup 6.x or later
; Download from: https://jrsoftware.org/isdl.php

#define MyAppName "DMX Master"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Truong Cong Dinh"
#define MyAppURL "https://github.com/truongcongdinh/DMXMaster"
#define MyAppExeName "DMXMaster.exe"
#define MyAppEmail "truongcongdinh97tcd@gmail.com"

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
AppContact={#MyAppEmail}

; Installation defaults
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes

; Output settings
OutputDir=installer_output
OutputBaseFilename=DMXMaster_Setup_v{#MyAppVersion}
SetupIconFile=assets\DMXMaster.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression
Compression=lzma2/max
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMADictionarySize=1048576

; Privileges
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Visual appearance
WizardStyle=modern

; License and info
LicenseFile=LICENSE.txt
InfoBeforeFile=INSTALLATION_INFO.txt

; Version info
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Installation
VersionInfoCopyright=Copyright (C) 2025 {#MyAppPublisher}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Assets (always overwrite on update)
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Config templates (don't overwrite existing)
Source: "config\*"; DestDir: "{app}\config"; Flags: onlyifdoesntexist uninsneveruninstall recursesubdirs createallsubdirs

; Data folder (NEVER overwrite - preserve user data)
Source: "data\shows\example_show.json"; DestDir: "{app}\data\shows"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "data\audio\.gitkeep"; DestDir: "{app}\data\audio"; Flags: onlyifdoesntexist uninsneveruninstall

; Documentation
Source: "DEPLOYMENT.md"; DestDir: "{app}"; DestName: "README.txt"; Flags: ignoreversion isreadme
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Create directories with proper permissions
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\data\shows"; Permissions: users-modify
Name: "{app}\data\audio"; Permissions: users-modify
Name: "{app}\config"; Permissions: users-modify
Name: "{commonappdata}\{#MyAppName}"; Permissions: users-modify

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\DMXMaster.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{group}\User Guide"; Filename: "{app}\README.txt"

; Desktop shortcut (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\DMXMaster.ico"; Tasks: desktopicon

; Quick Launch shortcut (optional, Windows 7 and earlier)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\DMXMaster.ico"; Tasks: quicklaunchicon

[Registry]
; Register file associations (optional)
Root: HKA; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; Flags: uninsdeletekeyifempty
Root: HKA; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}\Settings"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletevalue

[Run]
; Launch application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up generated files on uninstall (but preserve user data)
Type: files; Name: "{app}\logs\*.log"
Type: dirifempty; Name: "{app}\logs"

[Code]
var
  DataDirPage: TInputDirWizardPage;
  
procedure InitializeWizard;
begin
  { Custom page to ask about preserving data }
  DataDirPage := CreateInputDirPage(wpSelectDir,
    'Preserve User Data', 'Keep your shows and settings during upgrade?',
    'If this is an upgrade, your existing shows, audio files, and settings will be preserved automatically.' + #13#10#13#10 +
    'Data location: {app}\data',
    False, '');
  DataDirPage.Add('');
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  { Skip data dir page - we always preserve it }
  Result := (PageID = DataDirPage.ID);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  OldDataPath, NewDataPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    { Create app data directory for license files }
    ForceDirectories(ExpandConstant('{commonappdata}\{#MyAppName}'));
    
    { Log installation }
    SaveStringToFile(ExpandConstant('{app}\install.log'), 
      'Installed: ' + GetDateTimeString('yyyy-mm-dd hh:nn:ss', #0, #0) + #13#10, 
      True);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataPath: String;
  MsgResult: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    DataPath := ExpandConstant('{app}\data');
    
    { Ask user if they want to keep their data }
    if DirExists(DataPath) then
    begin
      MsgResult := MsgBox(
        'Do you want to keep your show files and audio data?' + #13#10#13#10 +
        'Click YES to preserve your data (recommended for reinstall)' + #13#10 +
        'Click NO to delete everything',
        mbConfirmation, MB_YESNO);
      
      if MsgResult = IDNO then
      begin
        { User chose to delete data }
        DelTree(DataPath, True, True, True);
      end;
    end;
  end;
end;

function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES','', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  
  { Check if upgrade }
  if IsUpgrade() then
  begin
    if MsgBox('An existing installation was detected. Do you want to upgrade?' + #13#10#13#10 +
              'Your data files (shows, audio, settings) will be preserved.',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      UnInstallOldVersion();
    end else
    begin
      Result := False;
    end;
  end;
end;
