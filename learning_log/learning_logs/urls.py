# -*- coding: utf-8 -*-

"""learning_logs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from . import views

urlpatterns = [
	#主页
    url(r'^$', views.index,name='index'),
    #显示所有主题
    url(r'^topics$', views.topics,name='topics'),
    #根据ID显示单个主题
    url(r'^topics/(?P<topic_id>\d+)/$', views.topic,name='topic'),
    #用于添加新主题的网页
    url(r'^new_topic/$', views.new_topic,name='new_topic'),
    #用于添加新条目的页面
    url(r'^new_entry/(?P<topic_id>\d+)/$', views.new_entry,name='new_entry'),
    #用于编辑条目的页面
    url(r'^edit_entry/(?P<entry_id>\d+)/$', views.edit_entry,name='edit_entry'),
]
