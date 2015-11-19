1.0.1 to 1.1.0
==============
* Fixed some bugs with trailing Windows newlines and trailing commas that get added to header information by Excel.
* Fixed a bug with the settings dialog where when focus was lost on a field the display would get messed up.
* Added a feature to automatically scan the default directory when the app starts up.
* Upgraded to wxWidgets 3 series, and fixed a bug where selecting directories included the drive label.

1.0.0 to 1.0.1
==============
* Changed the installer to use `pynsist` instead of by-hand construction in Windows with NSIS.
