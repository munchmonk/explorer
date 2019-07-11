#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python2.7
# coding: utf-8

l1 = [1, 3, 5, 7, 9, 11]
l2 = [2, 4, 6, 7, 5, 8]

if any(i in l1 for i in l2):
	print('yes')
else:
	print('no')