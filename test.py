#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python2.7
# coding: utf-8

a = 'water_mid_0.png'
b = 'water_mid_13.png'

import difflib

d = ''.join([s for s in difflib.ndiff(a, b) if s[0] != ' '])
d = ''.join([c for c in d if c not in '+-'])
d = d.replace(' ', '')

# print(str.isdigit(d))




def func(a):
	print(a[0], a[1])

# func((13, 12))


a = [1, 2, 3, 4, 5]
b = [2, 7]


a = 'level_2_3_3'
a = 'ciao'
b = 'mamma'
c = 'bye'

d = '_'.join([a, b, c])
print(d)
