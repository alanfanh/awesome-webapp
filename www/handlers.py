#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  处理Web API，返回json
import hashlib
import json
import logging
import re
import time

import markdown
from aiohttp import web
from coroweb import get, post
from models import User, Blog, Comment, next_id
from apis import Page, APIValueError, APIResourceNotFoundError, APIPermissionError, APIError
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
    value_l = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(value_l)


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
async def api_get_user(*, page="1"):
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


# 定义EMAIL和HASH格式规范
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


# 用户注册API
@post('/api/users')
async def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users = await User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, passwd)
    user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
                image='http://www.gravatar.com/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    await user.save()
    # make session cookie
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '*******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


# 获取日志列表API
@get('/api/blogs')
async def api_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)


# 获取日志详情API
@get('/api/blogs/{id}')
async def api_get_blog(*, pk):
    blog = await Blog.find(pk)
    return blog


# 发表日志API
@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__image,
                name=name.strip(), summary=summary.strip(), content=content.strip())
    await blog.save()
    return blog


# 编辑日志API
@post('/api/blogs/{id}')
async def api_update_blog(id, request, *, name, summary, content):
    check_admin(request)
    blog = await Blog.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    await blog.update()
    return blog


# 删除日志API
@post('/api/blogs/{id}/delete')
async def api_delete_blog(request, *, id):
    check_admin(request)
    blog = await Blog.find(id)
    await blog.remove()
    return dict(id=id)


# 删除用户API
@post('/api/users/{id}/delete')
async def api_delete_user(request, *, id):
    check_admin(request)
    id_buff = id
    user = await User.find(id)
    if user is None:
        raise APIResourceNotFoundError('comment')
    await user.remove()
    # 给被删除的用户在评论中标记
    comments = await Comment.findAll('user_id=?', [id])
    if comments:
        for comment in comments:
            id = comment.id
            c = await Comment.find(id)
            c.user_name = c.user_name + '(该用户已被删除)'
            await c.update()
    id = id_buff
    return dict(id=id)
