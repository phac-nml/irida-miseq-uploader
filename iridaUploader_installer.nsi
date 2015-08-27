RequestExecutionLevel admin
InstallDir $EXEDir


Section prerequisites

  SetOutPath "$INSTDIR"

  File ".\\prerequisites\\python-2.7.10.msi"
  ExecWait '"msiexec" /qb! /i "$INSTDIR\\python-2.7.10.msi" TARGETDIR=C:\Python27'


  File ".\\prerequisites\\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"
  ExecWait "$INSTDIR\\wxPython2.8-win32-unicode-2.8.12.1-py27.exe"


  File ".\\prerequisites\\iridaUploader-0.1.win32.msi"
  ExecWait '"msiexec" /qb! /i "$INSTDIR\\iridaUploader-0.1.win32.msi" TARGETDIR=C:\Python27'


SectionEnd


Section installmodules

  SetOutPath "$INSTDIR"

  File ".\\requirements.txt"
  ExecWait "C:\Python27\Scripts\pip.exe install -r $INSTDIR\\requirements.txt --allow-external pypubsub"

SectionEnd


Section postinstall

  SetOutPath "$INSTDIR"
  File ".\\post_installation.py"
  SetOutPath "$INSTDIR\iridaUploader"
  File ".\\iridaUploader\config.conf"
  SetOutPath "$INSTDIR"

  ExecWait "C:\\Python27\\pythonw.exe $INSTDIR\\post_installation.py"

SectionEnd


Section create_desktop_shortcut

  SetOutPath "$INSTDIR"
  File ".\\iridaUploader\GUI\images\\iu.ico"
  CreateShortCut "$DESKTOP\IRIDA Uploader.lnk" "C:\\Python27\\pythonw.exe" "C:\\Python27\\Lib\\site-packages\\iridaUploader\\run_IRIDA_Uploader.py" "$INSTDIR\iu.ico"

SectionEnd


Section create_startmenu_shortcut

  SetOutPath "$INSTDIR"
  File ".\\iridaUploader\GUI\images\\iu.ico"
  CreateDirectory "$SMPROGRAMS\iridaUploader"
  CreateShortCut "$SMPROGRAMS\IRIDA Uploader.lnk" "C:\\Python27\\pythonw.exe" "C:\\Python27\\Lib\\site-packages\\iridaUploader\\run_IRIDA_Uploader.py" "$INSTDIR\iu.ico"

SectionEnd