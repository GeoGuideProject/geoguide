# geoguide/server/config.py

import os
from decouple import config, Csv

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    """Base configuration."""
    SECRET_KEY = config('APP_KEY')
    DEBUG = config('DEBUG', False, cast=bool)
    BCRYPT_LOG_ROUNDS = config('BCRYPT_LOG_ROUNDS', 13, cast=int)
    DEBUG_TB_ENABLED = config('DEBUG_TB_ENABLED', False, cast=bool)
    DEBUG_TB_INTERCEPT_REDIRECTS = config(
        'DEBUG_TB_INTERCEPT_REDIRECTS', False, cast=bool)
    SQLALCHEMY_TRACK_MODIFICATIONS = config(
        'SQLALCHEMY_TRACK_MODIFICATIONS', False, cast=bool)
    UPLOADS_DEFAULT_DEST = config(
        'UPLOADS_DEFAULT_DEST', os.path.join(basedir, 'uploads'))
    GEOGUIDE_BOUNDARIES = config('GEOGUIDE_BOUNDARIES', '', cast=Csv(float))
    CHUNKSIZE = config('CHUNKSIZE', 50000, cast=int)
    USE_SQL = config('USE_SQL', False, cast=bool)
    JWT_ALGORITHM = config('JWT_ALGORITHM', default='HS256')
    JWT_EXPIRATION_SECONDS = config(
        'JWT_EXPIRATION_SECONDS', default=300, cast=int)
    JWT_REFRESH_EXPIRATION_SECONDS = config(
        'JWT_REFRESH_EXPIRATION_SECONDS', default=7 * 24 * 60 * 60, cast=int)
    JWT_AUTH_HEADER_PREFIX = config('JWT_AUTH_HEADER_PREFIX', default='JWT')
    BUNDLE_ERRORS = config('BUNDLE_ERRORS', default=True, cast=bool)


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = config('DEBUG', True, cast=bool)
    BCRYPT_LOG_ROUNDS = config('BCRYPT_LOG_ROUNDS', 4, cast=int)
    SQLALCHEMY_DATABASE_URI = config(
        'SQLALCHEMY_DATABASE_URI', 'sqlite:///' + os.path.join(basedir, 'dev.sqlite'))
    DEBUG_TB_ENABLED = config('DEBUG_TB_ENABLED', True, cast=bool)


class TestingConfig(BaseConfig):
    """Testing configuration."""
    DEBUG = config('DEBUG', True, cast=bool)
    TESTING = config('TESTING', True, cast=bool)
    BCRYPT_LOG_ROUNDS = config('BCRYPT_LOG_ROUNDS', 4, cast=int)
    SQLALCHEMY_DATABASE_URI = config('SQLALCHEMY_DATABASE_URI', 'sqlite:///')
    DEBUG_TB_ENABLED = config('DEBUG_TB_ENABLED', False, cast=bool)
    PRESERVE_CONTEXT_ON_EXCEPTION = config(
        'PRESERVE_CONTEXT_ON_EXCEPTION', False, cast=bool)


class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = config('DEBUG', False)
    SQLALCHEMY_DATABASE_URI = config(
        'SQLALCHEMY_DATABASE_URI', 'postgresql://localhost/example')
    DEBUG_TB_ENABLED = config('DEBUG_TB_ENABLED', False)
