# -*- coding: utf-8 -*-

"""users URL Configuration

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
from django.contrib.auth.views import login
from . import views

urlpatterns = [
	#登录页面
    url(r'^login/$', login,{'template_name':'users/login.html'},name='login'),
    #注销
    url(r'^logout/$', views.logout_view,name='logout'),
    #注册页面
    url(r'^register/$', views.register,name='register'),
]
