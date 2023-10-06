@echo off
:: This batch scripts opens a virtual environment (generates it if it does not exist) and starts the python program
SET ENVDIR=env
SET PYTHON_PROG_DIR=pypavlovupdater
SET PYTHON_PROGRAM=pavlovupdater.py
SET WINDOW_TIMEOUT=5
set WINDOW_TITLE="PyPavlovUpdater CLI"

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
START %WINDOW_TITLE% cmd.exe /k "cd %PYTHON_PROG_DIR% && python %PYTHON_PROGRAM% && timeout /t %WINDOW_TIMEOUT% && exit /b"