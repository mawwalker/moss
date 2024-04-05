# -*- coding: utf-8 -*-

import os
import tempfile
import wave
import shutil
import re
import time
import json
import yaml
import hashlib
import subprocess
# from . import constants, config
# from robot import logging
from pydub import AudioSegment
import logging
from pytz import timezone
import _thread as thread

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

do_not_bother = False
is_recordable = True

def get_file_content(filePath, flag="rb"):
    """
    读取文件内容并返回

    :param filePath: 文件路径
    :returns: 文件内容
    :raises IOError: 读取失败则抛出 IOError
    """
    with open(filePath, flag) as fp:
        return fp.read()


def check_and_delete(fp, wait=0):
    """
    检查并删除文件/文件夹

    :param fp: 文件路径
    """

    def run():
        if wait > 0:
            time.sleep(wait)
        if isinstance(fp, str) and os.path.exists(fp):
            if os.path.isfile(fp):
                os.remove(fp)
            else:
                shutil.rmtree(fp)

    thread.start_new_thread(run, ())


def write_temp_file(data, suffix, mode="w+b"):
    """
    写入临时文件

    :param data: 数据
    :param suffix: 后缀名
    :param mode: 写入模式，默认为 w+b
    :returns: 文件保存后的路径
    """
    with tempfile.NamedTemporaryFile(mode=mode, suffix=suffix, delete=False) as f:
        f.write(data)
        tmpfile = f.name
    return tmpfile


def get_pcm_from_wav(wav_path):
    """
    从 wav 文件中读取 pcm

    :param wav_path: wav 文件路径
    :returns: pcm 数据
    """
    wav = wave.open(wav_path, "rb")
    return wav.readframes(wav.getnframes())


def convert_wav_to_mp3(wav_path):
    """
    将 wav 文件转成 mp3

    :param wav_path: wav 文件路径
    :returns: mp3 文件路径
    """
    if not os.path.exists(wav_path):
        logger.critical(f"文件错误 {wav_path}", stack_info=True)
        return None
    mp3_path = wav_path.replace(".wav", ".mp3")
    AudioSegment.from_wav(wav_path).export(mp3_path, format="mp3")
    return mp3_path


def convert_mp3_to_wav(mp3_path):
    """
    将 mp3 文件转成 wav

    :param mp3_path: mp3 文件路径
    :returns: wav 文件路径
    """
    target = mp3_path.replace(".mp3", ".wav")
    if not os.path.exists(mp3_path):
        logger.critical(f"文件错误 {mp3_path}", stack_info=True)
        return None
    AudioSegment.from_mp3(mp3_path).export(target, format="wav")
    return target