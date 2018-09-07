#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'ctj'

import logging

from transwarp.web import get, view
from models import User, Blog, Comment

'''
@view('test_users.html'):返回一个Template对象，属性值如下：
	template_name：test_users.html
	model：dict(users=users)
@get('/')：返回函数：
	test_users.__web_route__:/
	test_users.__web_method__:GET
'''
@view('test_users.html')
@get('/')
def test_users():
	users = User.find_all()
	return dict(users=users)