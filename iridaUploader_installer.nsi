RequestExecutionLevel admin
InstallDir $EXEDir
Name "IRIDA Uploader"
Outfile "IRIDA_Uploader_Installer.exe"

Section prerequisites

  SetOutPath "$TEMP"

  File ".\prerequisites\python-2.7.10.msi"
  ExecWait '"msiexec" /qb! /i "$TEMP\python-2.7.10.msi" TARGETDIR=C:\Python27'


  File ".\prerequisites\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"
  ExecWait "$TEMP\wxPython2.8-win32-unicode-2.8.12.1-py27.exe /SILENT"


  File ".\prerequisites\iridaUploader-1.0.0.win32.msi"
  ExecWait '"msiexec" /qb! /i "$TEMP\iridaUploader-0.1.win32.msi" TARGETDIR=C:\Python27'


SectionEnd


Section installmodules

  SetOutPath "$TEMP"

  File ".\requirements.txt"
  ExecWait "C:\Python27\Scripts\pip.exe install -r $TEMP\requirements.txt --allow-external pypubsub"

SectionEnd


Section postinstall

  SetOutPath "$TEMP"
  File ".\post_installation.py"
  SetOutPath "$TEMP\iridaUploader"
  File ".\iridaUploader\config.conf"
  SetOutPath "$TEMP"

  ExecWait "C:\Python27\pythonw.exe $TEMP\post_installation.py"

SectionEnd


Section create_desktop_shortcut

  SetOutPath "$TEMP"
  File ".\iridaUploader\GUI\images\iu.ico"
  CreateShortCut "$DESKTOP\IRIDA Uploader.lnk" "C:\Python27\pythonw.exe" "C:\Python27\Lib\site-packages\iridaUploader\run_IRIDA_Uploader.py" "$TEMP\iu.ico"

SectionEnd


Section create_startmenu_shortcut

  SetOutPath "$TEMP"
  File ".\iridaUploader\GUI\images\iu.ico"
  CreateDirectory "$SMPROGRAMS\iridaUploader"
  CreateShortCut "$SMPROGRAMS\IRIDA Uploader.lnk" "C:\Python27\pythonw.exe" "C:\Python27\Lib\site-packages\iridaUploader\run_IRIDA_Uploader.py" "$TEMP\iu.ico"

SectionEnd
