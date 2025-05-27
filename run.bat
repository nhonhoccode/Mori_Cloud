@echo off
echo Dang khoi dong Memories-Keeping...

:: Kiem tra xem co thu muc venv khong
if not exist "venv" (
    echo Tao moi truong ao Python...
    python -m venv venv
)

:: Kich hoat moi truong ao
call venv\Scripts\activate

:: Di chuyen vao thu muc mori
cd Memories-Keeping/mori

:: Kiem tra xem co file requirements.txt khong
if exist "requirements.txt" (
    echo Cai dat cac thu vien Python...
    pip install -r requirements.txt
)

:: Chay migrations neu can
echo Chay migrations...
python manage.py makemigrations
python manage.py migrate

:: Khoi dong server
echo Khoi dong server Django...
python manage.py runserver

:: De cua so command prompt mo
pause 