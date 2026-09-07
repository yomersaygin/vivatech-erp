#define MyAppName "Vivatech ERP"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Vivatech"
#define MyAppExeName "VivatechERP.exe"

[Setup]
AppId={{5B8B0EC7-9FD4-4D6D-AE73-1C1696C9A580}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Vivatech ERP
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=VivatechERP-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\EXE\dist\VivatechERP.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\CONFIG\vivatech.json"; DestDir: "{app}\CONFIG"; Flags: ignoreversion
Source: "..\RUNTIME\FIRST-RUN-SETUP.ps1"; DestDir: "{app}\RUNTIME"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne Vivatech ERP kısayolu oluştur"; GroupDescription: "Ek görevler:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Vivatech ERP'yi başlat"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if WizardSilent then
    exit;
  if not FileExists(ExpandConstant('{pf}\Docker\Docker\Docker Desktop.exe')) then
  begin
    if MsgBox('Vivatech ERP, mevcut mimaride Docker Desktop gerektirir.' + #13#10 + #13#10 +
      'Docker Desktop bu bilgisayarda bulunamadı. Kuruluma yine de devam edilsin mi?',
      mbConfirmation, MB_YESNO) = IDNO then
      Result := False;
  end;
end;
