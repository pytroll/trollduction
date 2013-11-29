# -*- coding: utf-8 -*-
import logging
import logging.config

def get_logger(name):
    """
    Loads logger configuration from file and returns logger instance
    """
    try:
        logging.config.fileConfig('logger.cfg')
    except Exception as e:
        print e.message

    logger = logging.getLogger(name)
    return logger
    
    
    
def main():
    """
    """
    logger = get_logger('root')    
    # 'application' code
    logger.debug('debug message')
    logger.info('info message')
    logger.warn('warn message')
    logger.error('error message')
    logger.critical('critical message')

if __name__=='__main__':
    main()
