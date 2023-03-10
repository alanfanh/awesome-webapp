# webapp

> 本Web项目不基于任何成熟的Python Web开发框架，而是基于项目本身需求，实现了ORM、Model以及Web框架等基础架构。

## 介绍

项目完全基于Python协程，异步架构。aiohttp是基于asyncio实现的HTTP框架，本项目的Web框架基于aiohttp实现。

### Developer

[FanHao](http://alanfanh.github)

## 环境

### 语言

```text
python3.9.6 64bit
```

### 依赖

> 可使用"pip install -r requirements.txt"一键安装所有依赖项

````text
aiohttp==3.8.3
jinja2==3.1.2
aiomysql==0.1.1
markdown==3.4.1
````

### 数据库

> MySQL 8.0.31 Community Server - GPL

## 项目结构

> 持续更新中.....

```text
webapp
├── backup                            # 项目备份文件夹
├── conf                              # 项目配置文件
├── dist                              # 打包文件
├── ios                               # 存放ios App
├── LICENSE                           # license
├── www                               # 项目主代码文件夹
│   ├── static                        # 存放静态文件
│   ├── templates                     # 存放前端模版文件
│   ├── app.py
│   ├── model.py
│   └── orm.py
├── requirements.txt                  # 项目依赖
└── Readme.md                         # 项目Guide
```
