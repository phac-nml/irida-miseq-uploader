1.2.1 to 1.3.0
==============
* Added caching for some responses from the server so that we don't have to do a round-trip for every sample.
* Added default directory setting to settings panel.

1.2.0 to 1.2.1
==============
* Fixed a bug where empty fields in the header metadata section were being incorrectly parsed as read lengths.

1.1.0 to 1.2.0
==============
* Simplify searching for `SampleSheet.csv` using `os.walk`. Fixes a bug where Windows 7 junction points were being followed, and the OS was reporting permission denied errors on the junction points. This came from auto-scanning the default directory, and the default directory defaulting to the user's home directory.
* Add a license!
* Fix an issue where samples that have a common prefix would upload the wrong files for each sample (i.e., `Sample1`, `Sample11`, `Sample111` would all upload files for `Sample111`).

1.0.1 to 1.1.0
==============
* Fixed some bugs with trailing Windows newlines and trailing commas that get added to header information by Excel.
* Fixed a bug with the settings dialog where when focus was lost on a field the display would get messed up.
* Added a feature to automatically scan the default directory when the app starts up.
* Upgraded to wxWidgets 3 series, and fixed a bug where selecting directories included the drive label.

1.0.0 to 1.0.1
==============
* Changed the installer to use `pynsist` instead of by-hand construction in Windows with NSIS.
