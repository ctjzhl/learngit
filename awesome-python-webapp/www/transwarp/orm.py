#!/usr/bin/env python
# -*- coding: UTF-8 -*-

__author__ = 'Michael Liao'

'''
Database operation module. This module is independent with web module.
'''

import time,logging
import db

class Field(object):
	
	_count = 0

	def __init__ (self,**kw):
		self.name = kw.get('name',None)
		self._default = kw.get('default', None)
		self.primary_key = kw.get('primary_key', False)
		self.nullable = kw.get('nullable', False)
		self.updatable = kw.get('updatable', True)
		self.insertable = kw.get('insertable', True)
		self.ddl = kw.get('ddl', '')
		self._order = Field._count
		Field._count = Field._count + 1

	@property
	def default (self):
		d = self._default
		return d() if callable(d) else d
		
	def __str__ (self):
		s = ['<%s:%s,%s,default(%s),' % (self.__class__.__name__, self.name, self.ddl, self._default)]
		self.nullable and s.append('N')
		self.updatable and s.append('U')
		self.insertable and s.append('I')
		s.append('>')
		return ''.join(s)

class StringField(Field):
	def __init__ (self,**kw):
		if not 'default' in kw:
			kw['default'] = ''
		if not 'ddl' in kw:
			kw['ddl'] = 'varchar(255)'
		super(StringField,self).__init__(**kw)
		
class IntegerField(Field):
	def __init__ (self,**kw):
		if not 'default' in kw:
			kw['default'] = 0
		if not 'ddl' in kw:
			kw['ddl'] = 'bigint'
		super(IntegerField,self).__init__(**kw)
		
class FloatField(Field):
	def __init__ (self,**kw):
		if not 'default' in kw:
			kw['default'] = 0.0
		if not 'ddl' in kw:
			kw['ddl'] = 'real'
		super(FloatField,self).__init__(**kw)

class BooleanField(Field):
	def __init__ (self,**kw):
		if not 'default' in kw:
			kw['default'] = False
		if not 'ddl' in kw:
			kw['ddl'] = 'bool'
		super(BooleanField,self).__init__(**kw)



if __name__=='__main__':
	logging.basicConfig(level=logging.DEBUG)
	db.create_engine('root','root','test')
	db.update('drop table if exists user')
	db.update('create table user (id int primary key, name text, email text, passwd text, last_modified real)')
	import doctest
	doctest.testmod()