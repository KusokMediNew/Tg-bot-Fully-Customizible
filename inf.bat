@echo off
chcp 65001 >nul
set /p filename=Введите имя скрипта (без .py): 
:loop
python "%filename%.py"
goto loop
