# encoding=utf-8
from orm import Model
from orm import Field, StringFiled, IntegerField, BooleanField, FloatField, TextFiled


class User(Model):
    __table__ = 'users'
    id = IntegerField(primary_key=True)
    name = StringFiled()


class Blog(Model):
    __table__ = 'blogs'
    id = IntegerField(primary_key=True)
    name = StringFiled()


class Comment(Model):
    __table__ = 'comments'
    id = IntegerField(primary_key=True)
    Name = StringFiled()
    Comment = StringFiled()
