#!/usr/bin/env python
# -*- coding: utf-8 -*-

import types, os, re, cgi, sys, time, datetime, functools, mimetypes, threading, logging, urllib, traceback

try:
	from cStringIO import StringIO
except ImportError:
	from StringIO import StringIO

ctx = threading.local()

class Dict(dict):
	'''
	Simple dict but support access as x.y style

	>>> d1 = Dict()
	>>> d1['x'] = 100
	>>> d1.x
	100
	>>> d1.y = 200
	>>> d1['y']
	200
	>>> d2 = Dict(a=1,b=2,c='3')
	>>> d2.c
	'3'
	>>> d2['empty']
	Traceback (most recent call last):
		...
	KeyError: 'empty'
	>>> d2.empty
	Traceback (most recent call last):
		...
	AttributeError: 'Dict' object has no attribute 'empty'
	>>> d3 = Dict(('a','b','c'),(1,2,3))
	>>> d3.a
	1
	>>> d3.b
	2
	>>> d3.c
	3
	'''
	def __init__ (self,names=(),values=(),**kw):
		super(Dict,self).__init__(**kw)
		'''
			zip()将两个list糅合在一起 例如：
			x=[1,2,3,4,5]
			y=[6,7,8,9,10]
			zip(x,y)-->就得到了[(1,6),(2,7),(3,8),(4,9),(5,10)]
		'''
		for k,v in zip(names,values):
			self[k] = v
	def __getattr__ (self,key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Dict' object has no attribute '%s'" % key)
	def __setattr__ (self,key,value):
		self[key] = value

_TIMEDELTA_ZERO = datetime.timedelta(0)
_RE_TZ = re.compile('^([\+\-])([0-9]{1,2})\:([0-9]{1,2})$')

class UTC(datetime.tzinfo):
	def __init__ (self,utc):
		utc = str(utc.strip().upper())
		mt = _RE_TZ.match(utc)
		if mt:
			minus = mt.group(1)=='-'
			h = int(mt.group(2))
			m = int(mt.group(3))
			if minus:
				h,m = (-h), (-m)
			self._utcoffset = datetime.timedelta(hours=h, minutes=m)
			self._tzname = 'UTC%s' % utc
		else:
			raise ValueError('bad utc time zone')

	def utcoffset(self, dt):
		return self._utcoffset

	def dst (self,dt):
		return _TIMEDELTA_ZERO
			
	def tzname (self,dt):
		return self._tzname
		
	def __str__ (self):
			return 'UTC tzinfo object (%s)' % self._tzname
	
	__repr__ = __str__


if __name__ == '__main__':
	
	tz0 = UTC('+00:00')
	print tz0.tzname(None)

	logging.basicConfig(level=logging.DEBUG)
	sys.path.append('.')
	import doctest
	doctest.testmod()
