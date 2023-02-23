#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  处理Web API，返回json

from apis import APIPermissionError
from coroweb import get, post
from models import User


def check_admin(reqeust):
    # 检查是否管理员
    if reqeust.__user__ is None or not reqeust.__user__.admin:
        raise APIPermissionError


def get_page_index(page_str):
    # 获取页码
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass


@get('/')
async def index(request):
    users = await User.findAll()
    return {
        '__template__': 'test.html',
        'users': users
    }


@get('/api/users')
def api_get_user(*, page="1"):
    pass
