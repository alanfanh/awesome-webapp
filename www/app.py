# encoding=utf-8
import time
import json
import os
import asyncio
import orm
import logging
from aiohttp import web
from datetime import datetime
from config import configs
from coroweb import add_static, add_routes
from jinja2 import FileSystemLoader, Environment

logging.basicConfig(level=logging.INFO)


def init_jinja2(app, **kw):
    # 初始化jinja2函数
    logging.info("init jinja2")
    options = dict(
        autoescape=kw.get('autoescape', True),
        block_start_string=kw.get('block_start_string', "{%"),
        block_end_string=kw.get('block_end_string', "%}"),
        variable_start_string=kw.get('variable_start_string', "{{"),
        variable_end_string=kw.get('variable_end_string', "}}"),
        auto_reload=kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    logging.info('set jinja2 templates path:%s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env


# middleware，将通用功能从每个url处理函数中拿出来集中到一个地方
async def logger_factory(app, handler):
    # url日志处理工厂
    async def logger(request):
        logging.info('Request:%s %s' % (request.method, request.path))
        return await handler(request)
    return logger


async def auth_factory(app, handler):
    # 认证处理工厂，把当前用户绑定到request上，并对URL/mange/进行拦截
    # 检查当前用户是否为管理员用户
    async def auth(request):
        logging.info('check user:%s %s' % (request.method, request.path))
        request.__user__ = None
        pass
    return auth


async def data_factory(app, handle):
    # 数据处理工厂
    async def parse_data(request):
        if request.method == "POST":
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()
                logging.info('request json: %s' % str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request from: %s' % str(request._data__))
        return await handle(request)
    return parse_data


async def response_factory(app, handle):
    # 响应返回处理工厂函数
    async def response(request):
        logging.info('Response handle...')
        r = await handle(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(body=json.dump(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                # r['__user__'] = request.__user__
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and 100 <= r < 600:
            return web.Response()
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and 100 <= t < 600:
                return web.Response(t, str(m))
        # default
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response


def datetime_filter(t):
    # 时间转换
    delta = int(time.time() - t)
    if delta < 60:
        return '1分钟前'
    if delta < 3600:
        return '%s分钟前' % (delta//60)
    if delta < 86400:
        return '%s小时前' % (delta//3600)
    if delta < 604800:
        return '%s天前' % (delta//86400)
    dt = datetime.fromtimestamp(t)
    return '%s年%s月%s日' % (dt.year, dt.month, dt.day)


async def init(loop1):
    # web服务初始化
    await orm.create_pool(loop=loop1, **configs.db)
    app = web.Application(middlewares=[
        logger_factory, response_factory
    ])
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_static(app)
    add_routes(app, 'handlers')
    runner = web.AppRunner(app)
    await runner.setup()
    srv = web.TCPSite(runner, 'localhost', 8000)
    logging.info('server run in http://127.0.0.1:8000')
    await srv.start()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    loop.run_forever()
