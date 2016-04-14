1.5.0 to 1.6.0
==============

1.4.0 to 1.5.0
==============
* Changed the `Makefile` so that the uploader can be hacked on in other Linux distros, specifically Arch (thanks to @eric.enns)
* Fixed a UI issue where upload labels were overlapping in some cases (thanks to @eric.enns)
* Fixed an issue where the uploader found files that had `SampleSheet.csv` *anywhere* in the filename (i.e., `old_SampleSheet.csv`), now it matches **exactly** `SampleSheet.csv`.
* Changed the label `Upload speed` to `Average upload speed` to more accurately reflect the value we're reporting.
* Added support for resuming uploads on failure. If the uploader fails when uploading a run, it will now skip any files that were already uploaded.
* Added better error reporting when the uploader can't find the files for the sample by including the directory to help find issues.

1.4.0 to 1.4.1
==============
* Fix a performance regression when scanning directories for fastq files (thanks to @eric.enns)

1.3.0 to 1.4.0
==============
* Use [pytest](https://www.pytest.org) for testing instead of the custom testing framework build arount `unittest`.
* Add a feature to check the github repository for new releases.
* Add a menu File > Exit menu for familiarity.
* Use a wx widget for directory selection instead of building our own.
* Sample sheet parsing happens with a state machine instead of guessing sections based on number of columns.
* Extensive refactoring to move application functionality out of the GUI layer.

1.2.1 to 1.3.0
==============
* Added caching for some responses from the server so that we don't have to do a round-trip for every sample.
* Added default directory setting to settings panel.
* Limiting depth of directory scanning to 2 levels.

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
