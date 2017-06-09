import argparse
from shutil import copyfile
from os.path import isfile
from decouple import config
from random import choice


def new_key():
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    return ''.join(choice(chars) for i in range(50))


def set_key(key):
    if not isfile('.env'):
        copyfile('.env.example', '.env')
    with open('.env', 'r') as f:
        c = f.read()
    c = c.replace(pattern(), 'APP_KEY={}'.format(key))
    with open('.env', 'w') as f:
        f.write(c)


def pattern():
    key = config('APP_KEY', '')
    return 'APP_KEY={}'.format(key)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--show', help='show the generated key')
    args = parser.parse_args()

    key = new_key()

    if args.show:
        print(key)
        exit()

    set_key(key)
