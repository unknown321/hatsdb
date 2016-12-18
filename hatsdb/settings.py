# -*- coding: utf-8 -*-
# Django settings for hatsdb project.
#              ██                        
#              ▀▀       ██               
# ▄▄█████▄   ████     ███████    ▄████▄  
# ██▄▄▄▄ ▀     ██       ██      ██▄▄▄▄██ 
#  ▀▀▀▀██▄     ██       ██      ██▀▀▀▀▀▀ 
# █▄▄▄▄▄██  ▄▄▄██▄▄▄    ██▄▄▄   ▀██▄▄▄▄█ 
#  ▀▀▀▀▀▀   ▀▀▀▀▀▀▀▀     ▀▀▀▀     ▀▀▀▀▀  
#-------------------------------------------

DEBUG = False
TEMPLATE_DEBUG = DEBUG
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
      ('', ''),
)

MANAGERS = ADMINS

#URL_PREFIX = 'mongobase/'
DATABASES = {
    # 'default': 
    # {
    #     'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
    #     'NAME': '/home/hatsdb/users.sqlite3'                      # Or path to database file if using sqlite3.
    # },
    'default': 
    {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'site',
        'USER': 'root',
        'PASSWORD': '',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Moscow'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True




###########
# MEDIA - USER - no user content will be uploaded EVER
# STATIC - ADMIN
###########




# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = '' #NONE


# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '' #NONE


# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',   #for ajax
    'mongobase.context_processors.debug_var',
)

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATIC_ROOT = "/home/hatsdb/static/"

STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    "/home/hatsdb/assets/",   # where our files are, we'll copy em into STATIC_URL dir via `python manage.py collectstatic`
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'dajaxice.finders.DajaxiceFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'mongobase.loggingMiddleware.loggingMiddleware',

)

AUTHENTICATION_BACKENDS = (
    'django_openid_auth.auth.OpenIDBackend',
    'django.contrib.auth.backends.ModelBackend',
    )

ROOT_URLCONF = 'hatsdb.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'hatsdb.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '/home/hatsdb/templates',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mongobase',
    'django.contrib.humanize',
    'djangotoolbox',
    'django_openid_auth',
    'django.contrib.webdesign',
   # 'south',
    'dajaxice',              #for ajax
    'dajax'
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)s %(funcName)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(asctime)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'data_coll_log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/home/hatsdb/logs/data_collectors.log',
            'formatter':'simple'
        },
        'scanner_ids_log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/home/hatsdb/logs/scanner_ids.log',
            'formatter':'simple'
        },
        'scanner_log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/home/hatsdb/logs/scanner.log',
            'formatter':'simple'
        },
        'broken_hours_log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/home/hatsdb/logs/broken_hours.log',
            'formatter':'simple'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'mongobase.data_collectors': {
            'handlers': ['data_coll_log'],
            'level': 'DEBUG',

        },
        'mongobase.tasks': {
            'handlers': ['scanner_ids_log'],
            'level': 'DEBUG',

        },
        'mongobase.scanner': {
            'handlers': ['scanner_log'],
            'level': 'DEBUG',

        },
        'broken_hours': {
            'handlers': ['broken_hours_log'],
            'level': 'DEBUG',

        },
    }
}
OPENID_SSO_SERVER_URL = 'server-endpoint-url'
OPENID_SSO_SERVER_URL = 'https://steamcommunity.com/openid'
OPENID_CREATE_USERS = True
LOGIN_URL = '/openid/login/'
LOGIN_REDIRECT_URL = '/'
OPENID_FOLLOW_RENAMES = True
AUTH_PROFILE_MODULE = 'mongobase.userProfile'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'


BROKER_URL = ''
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_AMQP_TASK_RESULT_EXPIRES = 240
CELERY_MAX_CACHED_RESULTS = 500
CELERY_RESULT_PERSISTENT = False
# CELERY_IGNORE_RESULT = True
CELERY_STORE_ERRORS_EVEN_IF_IGNORED = False
CELERY_RESULT_BACKEND = "amqp"
CELERY_QUEUES = {"debian": {"binding_key": "debian_task",}}
CELERY_DEFAULT_EXCHANGE = "tasks"
CELERY_DEFAULT_EXCHANGE_TYPE = "direct"
CELERY_DEFAULT_ROUTING_KEY = "debian_task"
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = 'Etc/UTC'
CELERY_EVENT_QUEUE_TTL = 480
CELERY_EVENT_QUEUE_EXPIRES = 240
CELERY_TASK_RESULT_EXPIRES = 240


# EMAIL_USE_TLS = True
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_HOST_USER = ''
# EMAIL_HOST_PASSWORD = 'errorhandler'
# EMAIL_PORT = 587


#http://stackoverflow.com/questions/20301338/django-openid-auth-typeerror-openid-yadis-manager-yadisservicemanager-object-is
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'


#app-related settings
PREMIUM_LIMIT = 32
NONPREMIUM_LIMIT = 24
API_KEY = 

GAMES_LIST = ['tf2','dota2','csgo']
APPID_LIST = [440,570,730]


SID_PATTERN_OLD = 'STEAM_[0-9:]+'
SID_PATTERN_NEW = 'U:1:[0-9]+'
SID64_PATTERN = '[0-9]{17}'
MAGIC_SID = 76561197960265728       # default sid to substract
SORT_KEY = {'tf2':'Quality', 'dota2':'Rarity', 'csgo':'Quality'}
SPEC_FABRICATOR_START_DEFINDEX = 100000
PROF_FABRICATOR_START_DEFINDEX = 150000
CHEMSET_START_DEFINDEX = 200000
AUSTRALIUM_START_DEFINDEX = 300000
DOTA_GEM_START_DEFINDEX = 400000
DOTA_EXRECIPE_START_DEFINDEX = 500000
CSGO_STICKER_DEFINDEX = 600000
DOTA_GEM_DIV_STYLE = 'white-space: nowrap; padding: 3px;'
DEFAULT_CHARSET = 'utf-8'
CSGO_TOURNAMENT_COLOUR = 'ffd700'
CSGO_ITEM_DEFINDEX_START = 700000
TF2_INGNORED_STRANGE_PARTS = ['Kills', 'Sentry Kills', 'Kill Assists', 'Ubers','Carnival Underworld Kills',
                                'Carnival Games Won', 'Health Dispensed to Allies', 'Double Donks', 'Allies Teleported', 
                                'Teammates Whipped']
APPS = {'tf2':440, 'dota2':570, 'csgo':730}
DEFAULT_GUY_ID = 
AUTH_R = {'login':'', 'password':''}
AUTH_W = {'login':'', 'password':''}
UNUSUAL_QUALITIES = {'tf2':[5], 'dota2':[3], 'csgo':[3,20]}
TOURNAMENT_QUALITIES = {'tf2':[], 'dota2':[12], 'csgo':[12]}
HIDDEN_QUALS = {'tf2':['Unique'], 'dota2':['Standard','Base'], 'csgo':['Normal']}

ALLOWED_HOSTS = ['hatsdb.com']
