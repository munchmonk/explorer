#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python2.7
# coding: utf-8

f = open('allpok.txt', 'r')

top = 0
for line in f.readlines():
	if len(line) > top:
		print(line, top)
		top = len(line)


# answer = Kangaskhan, 10 characters