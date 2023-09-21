"""
Django settings for CPM project.

Generated by 'django-admin startproject' using Django 4.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os
import time
from datetime import timedelta
from pathlib import Path

from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from django.template.context_processors import media

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure--84wnua&74*d%&%$d4-3p66izzby*e(!29w)p0%lc7_$&g7pl2'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    "rest_framework_swagger",
    'django_filters',
    'corsheaders',
    'user',
    'product.alibabacloud_product',
    'project',
    'django_apscheduler',
    'cron.base_cron',
    'cron.alibabacloud_cron',
    'cron.aws_cron',
    'cron.gcp_cron',
    'cron.azure_cron',
    'message',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # 跨域
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 5,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # 'DEFAULT_PERMISSION_CLASSES': (
    #     # 将全局权限控制方案设置为仅允许认证用户访问
    #     'rest_framework.permissions.IsAuthenticated',
    # ),
}

# 跨域增加忽略
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True

CORS_ALLOW_HEADERS = (
    'XMLHttpRequest',
    'X_FILENAME',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'Pragma',
)

# Token 有效期
SIMPLE_JWT = {
    # token 过期时间 1h
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=10),
}

ROOT_URLCONF = 'config.urls'

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DJANGO_POSTGRES_DATABASE') or 'cpm',
        'USER': os.environ.get('DJANGO_POSTGRES_USER') or 'postgres',
        'PASSWORD': os.environ.get('DJANGO_POSTGRES_PASSWORD') or 'sunway',
        'HOST': os.environ.get('DJANGO_POSTGRES_HOST') or '127.0.0.1',
        'PORT': int(os.environ.get('DJANGO_POSTGRES_PORT') or 5432),
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'dist/'

STATICFILES_DIRS = [os.path.join(BASE_DIR, "dist/"),]

STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static')

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

PAGINATOR = {
    'max_page_size': 50,
    'page_index': 'page_index',
    'page_size': 'page_size'
}

cur_path = os.path.dirname(os.path.realpath(__file__))  # log_path是存放日志的路径
log_path = os.path.join(os.path.dirname(cur_path), 'log')
if not os.path.exists(log_path):  # 如果不存在这个logs文件夹，就自动创建一个
    os.mkdir(log_path)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,  # 表示是否禁用所有的已经存在的日志配置
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] [%(levelname)s] %(message)s', "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "verbose": {  # 时间 哪个文件 哪一行 进程 线程 模块 方法 日志级别 日志
            "format": '%(asctime)s %(pathname)s:%(lineno)d %(process)d %(thread)d %(module)s:%(funcName)s '
                      '%(levelname)s: %(message)s', "datefmt": "%Y-%m-%d %H:%M:%S"
        },
    },
    'handlers': {
        'console': {  # 控制台输出
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',  # 可以向类似与sys.stdout或者sys.stderr的任何文件对象(file object)输出信息
            'stream': 'ext://sys.stdout',  # 文件重定向的配置，将打印到控制台的信息都重定向出去 python manage.py runserver >> /all.log
            'formatter': 'verbose'
        },
        'default': {  # 默认记录所有日志
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(log_path, 'all-{}.log'.format(time.strftime('%Y-%m-%d'))),
            'maxBytes': 1024 * 1024 * 5,  # 文件大小
            'backupCount': 2,  # 备份数
            'formatter': 'verbose',  # 输出格式
            'encoding': 'utf-8',  # 设置默认编码，否则打印出来汉字乱码
        },
        'info': {  # 输出info日志
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',  # 将日志消息写入文件filename
            'filename': os.path.join(log_path, 'info-{}.log'.format(time.strftime('%Y-%m-%d'))),
            'formatter': 'verbose',
            'maxBytes': 1024 * 1024 * 5,  # 文件大小
            'backupCount': 2,  # 备份份数
            'encoding': 'utf-8',  # 设置默认编码
        },
        'error': {  # 输出error日志
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(log_path, 'error-{}.log'.format(time.strftime('%Y-%m-%d'))),
            'maxBytes': 1024 * 1024 * 5,  # 文件大小
            'backupCount': 2,  # 备份数
            'formatter': 'verbose',  # 输出格式
            'encoding': 'utf-8',  # 设置默认编码
        },
    },
    'loggers': {
        'cpm': {  # 自定义logger # 上线之后可以把 'console' 移除
            'level': 'DEBUG',
            'handlers': ['error', 'info', 'console', 'default'],  # 控制台输出，同时往 info-{}.log error-{}.log all-{}.log 写入日志（如果level符合）
            'propagate': True,  # 是否向上一级logger实例传递日志信息
        },
        'django': {  # 在Django层次结构中的所有消息记录器
            'handlers': ['default', 'info'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request ': {  # 与请求处理相关的日志消息。5xx响应被提升为错误消息；4xx响应被提升为警告消息。
            'handlers': ['default', 'info'],
            'level': 'INFO',
            'propagate': False,
        },
        "django.server": {  # 由RunServer命令调用的服务器所接收的请求的处理相关的日志消息。HTTP 5XX响应被记录为错误消息，4XX响应被记录为警告消息，其他一切都被记录为INFO
            "level": "INFO",
            "handlers": ['default', 'info'],
            'propagate': False,
        },
        'django.db.backends': {  # 记录代码与数据库交互相关的日志，主要是执行的sql语句、查询参数及sql执行时间，但是不包括ORM框架初始化
            'handlers': ['default', 'info'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# https://apscheduler.readthedocs.io/en/3.x/modules/schedulers/background.html
# https://github.com/agronholm/apscheduler
# https://apscheduler.readthedocs.io/en/3.x/modules/job.html
EXECUTORS = {
    "process_pool": ProcessPoolExecutor(max_workers=5),
    "thread_pool": ThreadPoolExecutor(max_workers=5),
}
JOB_DEFAULTS = {
    "coalesce": False,  # whether to only run the job once when several run times are due
    "misfire_grace_time": None,  # the time (in seconds) how much this job’s execution is allowed to be late (None means “allow the job to run no matter how late it is”)
    "max_instances": 1,  # the maximum number of concurrently executing instances allowed for this job
    "replace_existing": True,
}
JOB_TIMEZONE = 'Asia/Hong_Kong'
SCHEDULER_AUTOSTART = True

ENDPOINT = {
    "ECS_ENDPOINT": {
        "mainland": 'ecs-cn-hangzhou.aliyuncs.com',
        "oversea": 'ecs.cn-hongkong.aliyuncs.com'
    },
    "WAF_ENDPOINT": {
        "mainland": 'wafopenapi.cn-hangzhou.aliyuncs.com',
        "oversea": 'wafopenapi.ap-southeast-1.aliyuncs.com'
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST') or ''
EMAIL_PORT = os.environ.get('EMAIL_PORT') or 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER') or ''
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD') or ''
EMAIL_FROM = 'Service'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


RECIPIENT_ADDRESS = {
    "",
}
