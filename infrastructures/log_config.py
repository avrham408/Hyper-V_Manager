import infrastructures
import logging.config
import os



LOG_PATH = os.path.join(os.path.dirname(infrastructures.__path__[0]), "log")
LOG_FILENAME = 'infrastructures.log'

LOGGING_CONFIG = { 
	'version': 1,
	'disable_existing_loggers': True,
	'formatters': { 
		'standard': { 
			'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
		},
	},
	'handlers': { 
		's_handler': { 
			'level': 'DEBUG',
				'formatter': 'standard',
		    'class': 'logging.StreamHandler',
		    'stream': 'ext://sys.stdout',  # Default is stderr
		},
		'f_handler': { 
			'level': 'INFO',
			"class": "logging.handlers.RotatingFileHandler",
			"filename": f"{os.path.join(LOG_PATH, LOG_FILENAME)}",
			'formatter': 'standard',
			'class': 'logging.FileHandler',
			"encoding": "utf8"
		}
	},
	'loggers': { 
		"" : {  # root logger
	    'handlers': ['s_handler', 'f_handler'],
	    'level': 'DEBUG',
		}
	} 
}

logging.config.dictConfig(LOGGING_CONFIG)







