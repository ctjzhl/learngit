#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'ctj'

import logging

from transwarp.web import get, view
from models import User, Blog, Comment

@view('test_users.html')
@get('/')
def test_users():
	logging.info(111111111111111111111111111111)
	users = User.find_all()
	return dict(users=users)