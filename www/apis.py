#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON API definition
"""


class Page(object):
    """建立Page类来处理分页,可以在page_size更改每页项目的个数"""
    def __init__(self, item_count, page_index=1, page_size=8):
        self.item_count = item_count
        self.page_size = page_size
        self.page_count = item_count // page_size + (1 if item_count % page_size > 0 else 0)
        if (item_count == 0) or (page_index > self.page_count):
            self.offset = 0
            self.limit = 0
            self.page_index = 1
        else:
            self.page_index = page_index
            self.offset = self.page_size * (page_index - 1)
            self.limit = self.page_size
        self.has_next = self.page_index < self.page_count
        self.has_previous = self.page_index > 1

    def __str__(self):
        t = (self.item_count, self.page_count, self.page_index, self.page_size, self.offset, self.limit)
        return 'item_count:%s, page_count:%s, page_index:%s, page_size:%s, offset:%s, limit:%s' % t

    __repr__ = __str__


class APIError(Exception):
    """
    the base APIError which contains error(required), data(optional) and message(optional).
    """
    def __init__(self, error, data='', message='') -> None:
        super(APIError, self).__init__(message)
        self.error = error
        self.data = data
        self.message = message


class APIValueError(APIError):
    """
    Indicate the input value has error or invalid. The data specifies the error field of input form.
    """
    def __init__(self, field, message='') -> None:
        super(APIValueError, self).__init__('value:invalid', field, message)


class APIResourceNotFoundError(APIError):
    """
    Indicate the source was not found. The data specifies the resource name.
    """
    def __init__(self, field, message='') -> None:
        super(APIResourceNotFoundError, self).__init__('value:notfound', field, message)


class APIPermissionError(APIError):
    """
    Indicate the api have no permission
    """
    def __init__(self, message='') -> None:
        super(APIPermissionError, self).__init__('permission:forbidden', 'permission', message)
