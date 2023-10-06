# PyPavlovUpdater
Python program to update and subscribe to Pavlov mods. 
<br><br><br>
This program does 3 things:
1) Check the users subscribed mods against the installed mods, then update out of date mods
2) Install mods that are subscribed to but not installed
3) Subscribe to any mod that is installed but not currently subscribed to.

### Installation
Clone this repository onto your computer, then run the CLI Interface or the GUI Interface (not finished) batch files. The batch scripts will create a virtual environment (python base installation must have virtualenv installed) and will use it to run the program. 

### CLI Interface
The CLI interface can be launched by running `update_pavlov_mods_cli.bat`. The program will prompt the user for:
1) A Mod.io API token (with read+write privaleges) obtained from https://mod.io/me/access
2) The directory location for the Pavlov mod folder (usually `C:\Users\__user__\AppData\Local\Pavlov\Saved\Mods` but may vary for your installation)

The program will then get the users subscribed Pavlov mods from Mod.io, get the locally installed mods from the Pavlov mod folder, and compare the two lists against eachother. When out-of-date mods or not installed are detected, the mods are automatically downloaded. When a mod that is downloaded but not subscribed to is detected, the mod is automatically subscribed to. 