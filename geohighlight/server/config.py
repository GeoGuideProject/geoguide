# geohighlight/server/config.py

import os
from decouple import config

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    """Base configuration."""
    SECRET_KEY = config('APP_KEY')
    DEBUG = False
    BCRYPT_LOG_ROUNDS = 13
    DEBUG_TB_ENABLED = False
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    BCRYPT_LOG_ROUNDS = 4
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'dev.sqlite')
    DEBUG_TB_ENABLED = True


class TestingConfig(BaseConfig):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    BCRYPT_LOG_ROUNDS = 4
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
    DEBUG_TB_ENABLED = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False


class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/example'
    DEBUG_TB_ENABLED = False
