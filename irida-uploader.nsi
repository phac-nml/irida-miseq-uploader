[% extends "pyapp_w_pylauncher.nsi" %]
; from nsis documentation: http://nsis.sourceforge.net/Auto-uninstall_old_before_installing_new

[% block sections %]
[[ super() ]]
Function .onInit
 
  ReadRegStr $R0 HKLM \
  "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" \
  "UninstallString"
  StrCmp $R0 "" done
 
  MessageBox MB_OKCANCEL|MB_ICONINFORMATION \
  "${PRODUCT_NAME} is already installed. $\n$\nThe old version will be uninstalled \
  before installing ${PRODUCT_VERSION}. Click OK to remove the \
  old version or Cancel to cancel the upgrade." \
  IDOK uninst
  Abort
 
;Run the uninstaller
uninst:
  ClearErrors
  ExecWait '$R0 _?=$INSTDIR' ;Do not copy the uninstaller to a temp file
 
  IfErrors no_remove_uninstaller done
    ;You can either use Delete /REBOOTOK in the uninstaller or add some code
    ;here to remove the uninstaller. Use a registry key to check
    ;whether the user has chosen to uninstall. If you are using an uninstaller
    ;components page, make sure all sections are uninstalled.
  no_remove_uninstaller:
 
done:
 
FunctionEnd

[% endblock sections %]
