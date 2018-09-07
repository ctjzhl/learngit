#!/usr/bin/env python
#-*-coding:utf-8-*-

__author__='ctj'

'''
	数据库操纵模块,文档测试 >>>后边必须有个空格
'''
import time,uuid,functools,threading,logging
#reload(sys)
#sys.setdefaultencoding('utf8')

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

def next_id (t=None):
	'''
	Return next id as 50-char string
	
	Args:
		t:unix timestamp, default to None and using time.time().
	'''
	if t is None:
		t = time.time()
		'''
			%015d:15位的整型，不够15位，前置补0
			uuid4()  make a random UUID 得到一个随机的UUID
			如果没有传入参数根据系统当前时间15位和一个随机得到的UUID 填充3个0 组成一个长度为50的字符串
		'''
	return '%015d%s000'%(int(t*1000),uuid.uuid4().hex)

def _profiling (start,sql=''):
		t = time.time()-start
		if t>0.1:
			logging.warning('[PROFILING] [DB] %s: %s' % (t, sql))
		else:
			logging.info('[PROFILING] [DB] %s: %s' % (t, sql))

class DBError(Exception):
	pass
	

class MultiColumnsError(DBError):
	pass

#global engine object 保存着mysql数据库的连接
engine = None

#数据库引擎对象
class _Engine(object):
	def __init__ (self,connect):
		self._connect = connect
	def connect (self):
		return self._connect()

#创建引擎
def create_engine (user,password,database,host='127.0.0.1',port=3306,**kw):
	import mysql.connector
	global engine
	if engine is not None:
		raise DBError('Engine is already initialized.')
	params = dict(user=user,password=password,database=database,host=host,port=port)
	defaults = dict(use_unicode=True, charset='utf8', collation='utf8_general_ci', autocommit=False)
	'''
		将defaults和kw中的键值对保存到params中 如果有一个key两边都存在那么保存kw的.
		pop函数会将key为k的键值对删除并且返回k对应的value 如果k在kw中不存在 那么将会返回v
	'''
	for k,v in defaults.iteritems():
		params[k] = kw.pop(k,v)
	#字典kw的键/值对更新到params里
	params.update(kw)
	params['buffered'] = True
	#在这里(lambda:mysql.connector.connect(**params))返回的是一个函数而不是一个connection对象
	engine = _Engine(lambda:mysql.connector.connect(**params))
	logging.info('Init mysql engine <%s> ok.' %hex(id(engine)))	
	

class _LasyConnection(object):
	def __init__ (self):
		self.connection = None

	def cursor (self):
		if self.connection is None:
			connection = engine.connect()
			logging.info('open connection <%s>...' %hex(id(connection)))
			self.connection = connection
		return self.connection.cursor()
	
	def commit (self):
		self.connection.commit()
	
	def rollback (self):
		self.connection.rollback()

	def cleanup (self):
		if self.connection:
			connection = self.connection
			self.connecion = None
			logging.info('close connection <%s>...' % hex(id(connection)))
			connection.close()

#接下来解决对于不同的线程数据库链接应该是不一样的 于是创建一个变量  是一个threadlocal 对象
class _DbCtx(threading.local):
	def __init__ (self):

		self.connection = None
		self.transactions = 0
	
	def is_init (self):
		return not self.connection is None

	def init (self):
		logging.info('open lazy connection...')
		self.connection = _LasyConnection()
		self.transactions = 0

	def cleanup (self):
		self.connection.cleanup()
		self.connection = None

	def cursor (self):
		return self.connection.cursor()

_db_ctx = _DbCtx()

#通过with语句让数据库链接可以自动创建和关闭
'''
	with 语句：
	with 后面的语句会返回 _ConnectionCtx 对象 然后调用这个对象的 __enter__方法得到返回值 返回值赋值给as后面的变量 然后执行
	with下面的语句 执行完毕后 调用那个对象的 __exit__()方法
'''
class _ConnectionCtx(object):
	def __enter__ (self):
		global _db_ctx
		self.should_cleanup = False
		if not _db_ctx.is_init():
			_db_ctx.init()
			self.should_cleanup = True
		return self

	def  __exit__(self,exctype,excvalue,traceback):
		global _db_ctx
		if self.should_cleanup:
			_db_ctx.cleanup()

def connection ():
	return _ConnectionCtx()
#采用装饰器的方法 让其能够进行共用同一个数据库连接
def with_connection (func):
	@functools.wraps(func)
	def _wrapper (*args,**kw):
		with _ConnectionCtx():
			return func(*args,**kw)
	return _wrapper

class _TransactionCtx(object): 
	def __enter__ (self):
		global _db_ctx
		self.should_close_conn = False
		if not _db_ctx.is_init():
			_db_ctx.init()
			self.should_close_conn = True
		_db_ctx.transactions = _db_ctx.transactions +1
		logging.info('begin transaction...' if _db_ctx.transactions==1 else 'join current transaction...')
		return self

	def __exit__ (self,exctype,excvalue,traceback):
		global _db_ctx
		_db_ctx.transactions = _db_ctx.transactions -1
		try:
			if _db_ctx.transactions==0:
				if exctype is None:
					self.commit()
				else:
					self.rollback()

		finally:
			if self.should_close_conn:
				_db_ctx.cleanup()

	def commit (self):
		global _db_ctx
		logging.info('commit transaction...')
		try:
			_db_ctx.connection.commit()
			logging.info('commit ok.')
		except:
			logging.warning('commit failed. try rollback...')
			_db_ctx.connection.rollback()
			logging.warning('rollback ok.')
			raise

	def rollback (self):
		global _db_ctx
		logging.warning('rollback transaction...')
		_db_ctx.connection.rollback()
		logging.info('rollback ok.')	

def transaction ():
	'''
	Create a transaction object so can use with statement:

	with transaction():
		pass
	>>> def update_profile(id, name, rollback):
	...		u = dict(id=id, name=name, email='%s@test.org' % name, passwd=name, last_modified=time.time())
	...		insert('user', **u)
	...		r = update('update user set passwd=? where id=?', name.upper(), id)
	...		if rollback:
	...			raise StandardError('will cause rollback...')
	>>> with transaction():
	...		update_profile(900301, 'Python', False)		
	>>> select_one('select * from user where id=?',900301).name
	u'Python'
	>>> with transaction():
	... 	update_profile(900302,'Ruby',True)
	Traceback (most recent call last):
		...
	StandardError: will cause rollback...
	>>> select('select * from user where id = ?',900302)
	[]
	'''
	return _TransactionCtx()

def with_transaction (func):
	'''
	A decorator that makes function around transaction.

	>>> @with_transaction
	... def update_profile(id,name,rollback):
	... 	u = dict(id=id, name=name, email='%s@test.org' % name, passwd=name, last_modified=time.time())
	... 	insert('user',**u)
	... 	r = update('update user set passwd=? where id = ?',name.upper(),id)
	... 	if rollback:
	... 		raise StandardError('will cause rollback...')
	>>> update_profile(8080,'Julia',False)
	>>> select_one('select * from user where id = ?',8080).passwd
	u'JULIA'
	>>> update_profile(9090,'Robert',True)
	Traceback (most recent call last):
		...
	StandardError: will cause rollback...
	>>> select('select * from user where id=?',9090)
	[]
	'''
	@functools.wraps(func)
	def _wrapper (*args,**kw):
		_start = time.time()
		with _TransactionCtx():
			return func(*args, **kw)
		_profiling(_start)
	return _wrapper

def _select(sql,first,*args):
	global _db_ctx
	cursor = None
	sql = sql.replace('?','%s')
	logging.info('SQL: %s, ARGS: %s' % (sql, args))
	try:
		cursor = _db_ctx.connection.cursor()
		cursor.execute(sql,args)
		if cursor.description:
			names = [x[0] for x in cursor.description]
		if first:
			values = cursor.fetchone()
			if not values:
				return None
			return Dict(names,values)
		return [Dict(names,x) for x in cursor.fetchall()]
	finally:
		if cursor:
			cursor.close()

@with_connection
def select_one(sql,*args):
	'''
	Execute select SQL and expected one result.
	If no result found, return None.
	If multiple results found, the first one returned.
	>>> u1 = dict(id=100, name='Alice', email='alice@test.org', passwd='ABC-12345', last_modified=time.time())
	>>> u2 = dict(id=101, name='Sarah', email='sarah@test.org', passwd='ABC-12345', last_modified=time.time())
	>>> insert('user',**u1)
	1
	>>> insert('user',**u2)
	1
	>>> u = select_one('select * from user where id=?',100)
	>>> u.name
	u'Alice'
	>>> select_one('select * from user where email=?','abc@email.com')
	>>> u2 = select_one('select * from user where passwd=? order by email','ABC-12345')
	>>> u2.name
	u'Alice'
	'''
	return _select(sql,True,*args)

@with_connection
def select_int (sql,*args):
	'''
	Execute select SQL and expected one int and only one int result. 

	>>> n = update('delete from user')
	>>> u1 = dict(id=96900, name='Ada', email='ada@test.org', passwd='A-12345', last_modified=time.time())
	>>> u2 = dict(id=96901, name='Adam', email='adam@test.org', passwd='A-12345', last_modified=time.time())
	>>> insert('user',**u1)
	1
	>>> insert('user', **u2)
	1
	>>> select_int('select count(*) from user')
	2
	>>> select_int('select count(*) from user where email=?', 'ada@test.org')
	1
	>>> select_int('select count(*) from user where email=?', 'notexist@test.org')
	0
	>>> select_int('select id from user where email=?', 'ada@test.org')
	96900
	>>> select_int('select id, name from user where email=?', 'ada@test.org')
	Traceback (most recent call last):
		...
	MultiColumnsError: Expect only one column.
	'''
	d = _select(sql,True,*args)
	if len(d)!=1:
		raise MultiColumnsError('Expect only one column.')
	return d.values()[0]
	
@with_connection
def select(sql,*args):
	'''
	Execute select SQL and return list or empty list if no result.

	>>> u1 = dict(id=200, name='Wall.E', email='wall.e@test.org', passwd='back-to-earth', last_modified=time.time())
	>>> u2 = dict(id=201, name='Eva', email='eva@test.org', passwd='back-to-earth', last_modified=time.time())
	>>> insert('user', **u1)
	1
	>>> insert('user', **u2)
	1
	>>> L = select('select * from user where id=?', 900900900)
	>>> L
	[]
	>>> L = select('select * from user where id=?', 200)
	>>> L[0].email
	u'wall.e@test.org'
	>>> L = select('select * from user where passwd=? order by id desc', 'back-to-earth')
	>>> L[0].name
	u'Eva'
	>>> L[1].name
	u'Wall.E'

	'''
	return _select(sql,False,*args)

@with_connection
def _update (sql,*args):
	global _db_ctx
	cursor = None
	
	sql = sql.replace('?', '%s')
	logging.info('SQL: %s, ARGS: %s' % (sql, args))
	try:
		cursor = _db_ctx.connection.cursor()
		cursor.execute(sql, args)
		r = cursor.rowcount
		if _db_ctx.transactions==0:
			logging.info('auto commit')
			_db_ctx.connection.commit()
		return r
	finally:
		if cursor:
			cursor.close()


def insert (table,**kw):
	'''
	Execute insert SQL.

	>>> u1 = dict(id=2000, name='Bob', email='bob@test.org', passwd='bobobob', last_modified=time.time())
	>>> insert('user', **u1)
	1
	>>> u2 = select_one('select * from user where id=?', 2000)
	>>> u2.name
	u'Bob'
	>>> insert('user', **u2)
	Traceback (most recent call last):
		...
	IntegrityError: 1062 (23000): Duplicate entry '2000' for key 'PRIMARY'
	'''
	cols,args = zip(*kw.iteritems())
	sql = 'insert into `%s` (%s) values (%s)' % (table, ','.join(['`%s`' % col for col in cols]), ','.join(['?' for i in range(len(cols))]))
	return _update(sql, *args)	

def update (sql,*args):
	r'''
	Execute update SQL.

	>>> u1 = dict(id=1000, name='Michael', email='michael@test.org', passwd='123456', last_modified=time.time())
	>>> insert('user',**u1)
	1
	>>> u2 = select_one('select * from user where id=?', 1000)
	>>> u2.email
	u'michael@test.org'
	>>> u2.passwd
	u'123456'
	>>> update('update user set email=?, passwd=? where id=?', 'michael@example.org', '654321', 1000)
	1
	>>> u3 = select_one('select * from user where id=?', 1000)
	>>> u3.email
	u'michael@example.org'
	>>> u3.passwd
	u'654321'
	>>> update('update user set passwd=? where id=?', '***', '123\' or id=\'456')
	0
	'''
	return _update(sql, *args)





if __name__=='__main__':
	logging.basicConfig(level=logging.DEBUG)
	create_engine('www-data','www-data','awesome')

	sql = 'drop table if exists user'
	update(sql)
	update('create table user (id int primary key, name text, email text, passwd text, last_modified real)')
	import doctest
	doctest.testmod()
	


		
		