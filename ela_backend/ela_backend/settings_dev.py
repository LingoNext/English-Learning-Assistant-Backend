from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
DEBUG = True
APPEND_SLASH = False
ALLOWED_HOSTS = ['*']
SECURE_SSL_REDIRECT = False

# 這是測試開發環境的 Django 設定文件，使用 SQLite 作為數據庫，並且允許所有主機訪問
# 創建數據庫和應用遷移：
# cd ela_backend
# python manage.py makemigrations --settings=ela_backend.settings_dev
# python manage.py migrate --settings=ela_backend.settings_dev
# 運行開發伺服器：
# cd ela_backend ; python manage.py runserver --settings=ela_backend.settings_dev 8000