#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  处理Web API，返回json
import hashlib
import json
import logging
import time

import markdown
from aiohttp import web
from coroweb import get, post
from models import User, Blog, Comment
from apis import Page, APIValueError, APIResourceNotFoundError, APIPermissionError
from config import configs

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret


def check_admin(reqeust):
    # 检查是否管理员
    if reqeust.__user__ is None or not reqeust.__user__.admin:
        raise APIPermissionError


def get_page_index(page_str):
    # 获取页码信息
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p


def user2cookie(user, max_age):
    # 使用id-expires-sha1构建cookie字符串
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)


@get('/')
async def index(*, page='1'):
    # 处理首页URL
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        blogs = []
    else:
        blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return {
        '__template__': 'blogs.html',
        'page': p,
        'blogs': blogs
    }


@get('/blog/{id}')
async def get_blog(id):
    # 获取博文详情页面URL
    blog = await Blog.find(pk=id)
    comments = await Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
    for c in comments:
        c.html_content = markdown.markdown(c.content)
    blog.html_content = markdown.markdown(blog.content)
    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments
    }


@get('/register')
async def register():
    # 注册页面URL
    return {
        '__template__': 'register.html'
    }


@get('/signin')
async def signin():
    # 登录页面URL
    return {
        '__template__:' 'signin.html'
    }


@get('/api/authenticate')
async def authenticate(*, email, passwd):
    # 用户登录验证API
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid passwd.')
    users = await User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    # check passwd:
    user = users[0]
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.digest():
        raise APIValueError('passwd', 'Invalid passwd.')
    # Authenticate OK. set Cookies:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@get('/logout')
def logout(request):
    # 用户注销登录
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, "-deleted-", max_age=0, httponly=True)
    logging.info("user signed out.")
    return r


@get('/manage/')
def manage():
    # 管理页面
    return 'redirect:/manage/comments'


@get('/manage/comments')
def manage_comments(*, page='1'):
    # 评论管理页面
    return {
        "__template__": 'manage_comments.html',
        'page_index': get_page_index(page)
    }


@get('/manage/blog')
def manage_blogs(*, page='1'):
    # 博文管理页面
    return {
        '__template__': 'manage_blogs.html',
        'page_index': get_page_index(page)
    }


@get('/manage/blogs/create')
def manage_create_blog():
    # 创建博文页面
    return {
        '__template__': 'manage_blog_create.html'
    }


@get('/manage/blogs/edit')
def manage_edit_blog(*, id):
    # 编辑博文页面
    return {
        '__template__': 'manage_blog_edit.html',
        'id': id,
        'action': '/api/blogs/%s' % id
    }


@get('/manage/users')
def manage_users(*, page='1'):
    # 用户管理页面
    return {
        '__template__': 'manage_users.html',
        'page_index': get_page_index(page)
    }


@get('/api/comments')
async def api_comments(*, page='1'):
    # API，获取评论信息
    page_index = get_page_index(page)
    num = await Comment.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, comments=())
    comments = await Comment.findAll(orderBy='created by desc', limit=(p.offset, p.limit))
    return dict(page=p, comments=comments)


@post('/api/blog/{id}/comments')
async def api_create_comment(id, request, *, content):
    # API，用户发表评论
    user = request.__user__
    if user is None:
        raise APIPermissionError('Please sign in first.')
    if not content or not content.strip():
        raise APIValueError('content')
    blog = await Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    comment = Comment(blog_id=blog.id, user_id=user.id, user_name=user.name,
                      user_image=user.image, content=content.strip())
    await comment.save()
    return comment


@get('/api/comments/{id}/delete')
async def api_delete_comment(id, request):
    # 管理员用户删除评论
    check_admin(request)
    c = await Comment.find(id)
    if c is None:
        raise APIResourceNotFoundError('Comment')
    await c.remove()
    return dict(id=id)


@get('/api/users')
def api_get_user(*, page="1"):
    # 获取用户信息API
    page_index = get_page_index(page)
    num = await User.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, users=())
    users = await User.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    for u in users:
        u.passwd = '******'
    return dict(page=p, users=users)
