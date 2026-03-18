#define MyAppName      "Password Manager"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "Password Manager"
#define MyAppExeName   "PasswordManager.exe"
#define MyAppURL       ""

[Setup]
AppId={{8F4E9B1A-3C7D-4E2F-8A6B-1D5C3F9E2B4A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation directory
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output
OutputDir=installer_output
OutputBaseFilename=PasswordManagerSetup_{#MyAppVersion}
SetupIconFile=assets\favicon.ico

; License & disclaimer pages
LicenseFile=licence.txt
InfoBeforeFile=assets\disclaimer.txt

; Compression
Compression=lzma2/ultra64
SolidCompression=yes

; Visuals
WizardStyle=modern

; Minimum Windows version (Windows 10)
MinVersion=10.0

; Uninstall
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; Optionally add Turkish:
; Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; \
    Description: "Create a desktop shortcut"; \
    GroupDescription: "Additional shortcuts:"; \
    Flags: unchecked

[Files]
; Main executable (built by PyInstaller --onefile)
Source: "dist\{#MyAppExeName}"; \
    DestDir: "{app}"; \
    Flags: ignoreversion

[Icons]
; Start menu
Name: "{group}\{#MyAppName}"; \
    Filename: "{app}\{#MyAppExeName}"; \
    WorkingDir: "{app}"

; Uninstall entry in start menu
Name: "{group}\Uninstall {#MyAppName}"; \
    Filename: "{uninstallexe}"

; Desktop shortcut (optional, controlled by task above)
Name: "{autodesktop}\{#MyAppName}"; \
    Filename: "{app}\{#MyAppExeName}"; \
    WorkingDir: "{app}"; \
    Tasks: desktopicon

[Run]
; Offer to launch after installation
Filename: "{app}\{#MyAppExeName}"; \
    Description: "Launch {#MyAppName}"; \
    Flags: nowait postinstall skipifsilent

[UninstallRun]
; Nothing extra to run on uninstall

[Code]
// Remind the user that their data in %USERPROFILE%\pwapp is NOT removed on uninstall.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    MsgBox(
      'Uninstallation complete.' + #13#10 + #13#10 +
      'Your password database and settings stored in:' + #13#10 +
      '  ' + ExpandConstant('{%USERPROFILE}') + '\pwapp\' + #13#10 + #13#10 +
      'have NOT been removed.' + #13#10 +
      'Delete that folder manually if you wish to remove all data.',
      mbInformation,
      MB_OK
    );
  end;
end;
