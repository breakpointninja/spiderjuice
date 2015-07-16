import os
import platform

PRODUCTION = False

hostname = platform.uname()[1]
if hostname == 'linode-contify':
    PRODUCTION = True


BASE_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s %(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
        },
        'simple': {
            'class': 'logging.Formatter',
            'format': '%(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
        },
        'file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'DEBUG',
            'filename': os.path.join(BASE_PROJECT_DIR, 'logs/spiderjuice.log'),
            'formatter': 'detailed',
            'when': 'midnight',
            'backupCount': 60,
        },
        'mail': {
            'class': 'logging.handlers.SMTPHandler',
            'level': 'ERROR',
            'mailhost': 'smtp.gmail.com',
            'fromaddr': 'sitesadmin@contify.com',
            'toaddrs': 'rahul.verma@contify.com',
            'subject': 'Error in Spiderjuice',
            'credentials': ('sitesadmin@contify.com', 'Cont1fy#2013'),
            'secure': ()
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file'] if PRODUCTION else ['file']
    },
}

# Technically this should only be the default and we should use the encoding specified in the http header
HTTP_HEADER_CHARSET = 'ISO-8859-8'
DEFAULT_JOB_TIMEOUT_SECONDS = 300

MAX_RETRIES = 5