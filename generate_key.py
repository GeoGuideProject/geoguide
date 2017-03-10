from random import choice

chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'

print(''.join(choice(chars) for i in range(50)))
