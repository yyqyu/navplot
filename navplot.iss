[Setup]
AppName=NavPlot
AppVerName=NavPlot v0.4
DefaultDirName={pf}\Freeflight\NavPlot
LicenseFile=gpl.txt
ShowLanguageDialog=auto
DefaultGroupName=NavPlot
UninstallDisplayIcon={app}\navplot.ico
[Files]
Source: dist\MSVCR71.dll; DestDir: {app}
Source: dist\_controls_.pyd; DestDir: {app}
Source: dist\_core_.pyd; DestDir: {app}
Source: dist\_gdi_.pyd; DestDir: {app}
Source: dist\_hashlib.pyd; DestDir: {app}
Source: dist\_misc_.pyd; DestDir: {app}
Source: dist\_rl_accel.pyd; DestDir: {app}
Source: dist\_socket.pyd; DestDir: {app}
Source: dist\_ssl.pyd; DestDir: {app}
Source: dist\_windows_.pyd; DestDir: {app}
Source: dist\bz2.pyd; DestDir: {app}
Source: dist\gnavplot.exe; DestDir: {app}
Source: dist\gpl.txt; DestDir: {app}
Source: dist\library.zip; DestDir: {app}
Source: dist\map.dat; DestDir: {app}
Source: dist\navplot.ico; DestDir: {app}
Source: dist\pyexpat.pyd; DestDir: {app}
Source: dist\python25.dll; DestDir: {app}
Source: dist\readme.txt; DestDir: {app}
Source: dist\select.pyd; DestDir: {app}
Source: dist\sgmlop.pyd; DestDir: {app}
Source: dist\unicodedata.pyd; DestDir: {app}
Source: dist\w9xpopen.exe; DestDir: {app}
Source: dist\wxbase28uh_net_vc.dll; DestDir: {app}
Source: dist\wxbase28uh_vc.dll; DestDir: {app}
Source: dist\wxmsw28uh_adv_vc.dll; DestDir: {app}
Source: dist\wxmsw28uh_core_vc.dll; DestDir: {app}
Source: dist\wxmsw28uh_html_vc.dll; DestDir: {app}
[Icons]
Name: {group}\NavPlot; Filename: {app}\gnavplot.exe; WorkingDir: {app}; Comment: NOTAM download and display; Flags: createonlyiffileexists; IconFilename: {app}\navplot.ico; IconIndex: 0
[Registry]
Root: HKCU; Subkey: Software\Freeflight\NavPlot; Flags: uninsdeletekey dontcreatekey
