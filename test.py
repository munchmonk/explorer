#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python2.7
# coding: utf-8

def index_to_coord(indexes):
		x = indexes[0] * 32
		y = indexes[0] * 32

		print(x, y)

		return x, y



index_to_coord([2, 2])