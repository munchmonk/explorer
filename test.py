#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python2.7
# coding: utf-8

a = 'water_mid_0.png'
b = 'water_mid_13.png'

import difflib

d = ''.join([s for s in difflib.ndiff(a, b) if s[0] != ' '])
d = ''.join([c for c in d if c not in '+-'])
d = d.replace(' ', '')

# print(str.isdigit(d))


a = [0, 1, 2]
a.insert(10, 9)
a.insert(3, 8)
print(a)
