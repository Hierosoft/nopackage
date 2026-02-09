@ECHO OFF
SET VENV_DIR=%~dp0\..\..\hierosoft\.venv
IF NOT EXIST %VENV_DIR% GOTO GLOBALPY
%VENV_DIR%\Scripts\python %~dp0/nopackage %*
GOTO END
:GLOBALPY
py -3 %~dp0/nopackage %*
:END
if NOT ["%errorlevel%"]==["0"] (
    pause
    exit /b %errorlevel%
)