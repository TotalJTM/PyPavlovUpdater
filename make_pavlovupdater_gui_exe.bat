@echo off
:: This batch scripts opens a virtual environment (generates it if it does not exist) and starts the python program
SET ENVDIR=env
SET PYTHON_PROG_DIR=pypavlovupdater
SET PYTHON_PROGRAM=pavlovupdater_gui.py
SET WINDOW_TIMEOUT=20
set WINDOW_TITLE="PyPavlovUpdater Gui Installer"

:: Check if env can be started, create virtual env and install required packages if no env exists
IF EXIST %ENVDIR%\Scripts\activate ( SET RUN_ENV="true" )
IF %RUN_ENV%=="true" (
    CALL %ENVDIR%\Scripts\activate 
) ELSE (
    python -m virtualenv %ENVDIR%
    CALL %ENVDIR%\Scripts\activate
    IF EXIST %ENVDIR%\requirements.txt ( pip install -r requirements.txt )
)

:: Start PYTHON_PROGRAM from a new command window
START %WINDOW_TITLE% cmd.exe /k "cd %PYTHON_PROG_DIR% && pyinstaller %PYTHON_PROGRAM% --onefile -c && cd dist && rename pavlovupdater_gui.exe PyPavlovUpdater_GUI.exe && timeout /t %WINDOW_TIMEOUT% && exit /b"