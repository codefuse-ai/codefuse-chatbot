import textwrap, time, copy, random, hashlib, json, os
from datetime import datetime, timedelta
from functools import wraps
from loguru import logger
from typing import *
from pathlib import Path
from io import BytesIO
from fastapi import Body, File, Form, Body, Query, UploadFile
from tempfile import SpooledTemporaryFile
import json


DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def getCurrentDatetime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:00")


def addMinutesToTime(input_time: str, n: int = 5, dateformat=DATE_FORMAT):
    dt = datetime.strptime(input_time, dateformat)

    # 前后加N分钟
    new_time_before = dt - timedelta(minutes=n)
    new_time_after = dt + timedelta(minutes=n)
    return new_time_before.strftime(dateformat), new_time_after.strftime(dateformat)


def timestampToDateformat(ts, interval=1000, dateformat=DATE_FORMAT):
    '''将标准时间戳转换标准指定时间格式'''
    return datetime.fromtimestamp(ts//interval).strftime(dateformat)


def datefromatToTimestamp(dt, interval=1000, dateformat=DATE_FORMAT):
    '''将标准时间格式转换未标准时间戳'''
    return datetime.strptime(dt, dateformat).timestamp()*interval


def func_timer():
    '''
    用装饰器实现函数计时
    :param function: 需要计时的函数
    :return: None
    '''
    @wraps(function)
    def function_timer(*args, **kwargs):
        t0 = time.time()
        result = function(*args, **kwargs)
        t1 = time.time()
        logger.info('[Function: {name} finished, spent time: {time:.3f}s]'.format(
            name=function.__name__,
            time=t1 - t0
        ))
        return result
    return function_timer


def custom_serializer(obj):
    try:
        return str(obj)
    except TypeError:
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def read_jsonl_file(filename):
    data = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    return data


def save_to_jsonl_file(data, filename):
    dir_name = os.path.dirname(filename)
    if not os.path.exists(dir_name): os.makedirs(dir_name)

    with open(filename, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def read_json_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)
    
    
def save_to_json_file(data, filename):
    dir_name = os.path.dirname(filename)
    if not os.path.exists(dir_name): os.makedirs(dir_name)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=custom_serializer)


def file_normalize(file: Union[str, Path, bytes], filename=None):
    # logger.debug(f"{file}")
    if isinstance(file, bytes): # raw bytes
        file = BytesIO(file)
    elif hasattr(file, "read"): # a file io like object
        filename = filename or file.name
    else: # a local path
        file = Path(file).absolute().open("rb")
        # logger.debug(file)
        filename = filename or file.name
    return file, filename


def get_uploadfile(file: Union[str, Path, bytes], filename=None) -> UploadFile:
    temp_file = SpooledTemporaryFile(max_size=10 * 1024 * 1024)
    temp_file.write(file.read())
    temp_file.seek(0)
    return UploadFile(file=temp_file, filename=filename)


