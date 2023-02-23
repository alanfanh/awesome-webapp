#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON API definition
"""


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
