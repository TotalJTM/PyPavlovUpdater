# PyPavlovUpdater
Python program to update and subscribe to Pavlov-VR mods. 
<br><br><br>
This program does 3 main things:
1) Check the users subscribed mods against the installed mods, then update out of date mods
2) Install mods that are subscribed to but not installed
3) Subscribe to any mod that is installed but not currently subscribed to.

There is expanded functionality with a PySimpleGUI-based GUI to make downloading and viewing specific mods easier.

### Pavlov Versions Supported
This mod downloader currently only supports the PCVR version of Pavlov.

This mod downloader is meant to be used in a Windows environment and does not currently support other operating systems.

### Installation
Clone this repository onto your computer, then run the CLI Interface or the GUI Interface (not finished) batch files. The batch scripts will create a virtual environment (python base installation must have virtualenv installed) and will use it to run the program. 

### CLI Interface
The CLI interface can be launched by running `update_pavlov_mods_cli.bat`. The program will prompt the user for:
1) A Mod.io API token (with read+write privilege) obtained from https://mod.io/me/access
2) The directory location for the Pavlov mod folder (usually `C:\Users\__user__\AppData\Local\Pavlov\Saved\Mods` but may vary for your installation)

The program will then get the users subscribed Pavlov mods from Mod.io, get the locally installed mods from the Pavlov mod folder, and compare the two lists against eachother. 

When out-of-date mods or not installed are detected, the mods are automatically downloaded. When a mod that is downloaded but not subscribed to is detected, the mod is automatically subscribed to. 

This functionality is not being worked on and is not very usuable in its current state. When the GUI is "finished", ill remake this portion of the program with better command line support. 

### GUI Interface
The GUI interface can be launched by running `run_pavlovupdater_gui.bat` or by opening the `PyPavlovUpdater.exe` executable. 

The user will need to enter the same API token and mod folder directory listed above into the Options Menu. As of version 1.4, the mod folder directory is set to the default path for a Pavlov windows installation.

The user can then press the 'Open Download Menu' button to download uninstalled or outdated mods. A remove mod button is also provided to delete a specific mod (based on mods UGC).

Pressing the 'Open Subscribed Mod Manager' or 'Open Full Modlist Explorer' buttons will open a new window where the subscribed mods or full Pavlov modlist are displayed. Here, you can change a mods subscription status, rate a mod, and get a link to the mod page on mod.io. A filter input is also supplied so individual mods can be filtered by name, mod UGC, author or installation status.

#### Building the GUI Interface
The GUI is built using pyinstaller. To rebuild the GUI from python, use the `make_pavlovupdater_gui_exe.bat` script and get the executable from `pavlovupdater/dist`

### Notes About this Project
This project is not affiliated with the developers of Pavlov. Instead, this is a community driven project.

When downloading some mods, the zip file will appear corrupted to the program and will not be installed. These mods will need to be downloaded in game, it is normal for them to reappear in the download menu after a failed download/installation.