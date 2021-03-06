import logging
import os
import sys
import msgpack
import socket
import threading
import traceback

try:
    import json
except ImportError:
    import simplejson as json

from fluent import sender

class FluentRecordFormatter(object):
    def __init__(self, appname):
        self.hostname = socket.gethostname()
        self.appname = appname

    def formatException(self, exceptionInfo):
      eData = {}
      eData['type'] = str(exceptionInfo[0])
      eData['details'] = str(exceptionInfo[1])
      eData['trace'] = traceback.format_exc()
      return eData

    def format(self, record):
        try:
          exec_info = record.exc_info
        except AttributeError,e:
          exec_info = None
	data = {
          'app_name' : self.appname,
          'sys_host' : self.hostname,
          'sys_name' : record.name,
          'sys_module' : record.module,
          # 'sys_lineno' : record.lineno,
          # 'sys_levelno' : record.levelno,
          'sys_levelname' : record.levelname,
          # 'sys_filename' : record.filename,
          # 'sys_funcname' : record.funcName,
          'sys_exc_info' : record.exc_info,
        }
        if 'sys_exc_info' in data and data['sys_exc_info']:
           data['sys_exc_info'] = self.formatException(data['sys_exc_info'])
        else:
           del data['sys_exc_info']
        self._structuring(data, record.msg)
        return data

    def _structuring(self, data, msg):
        if isinstance(msg, dict):
            self._add_dic(data, msg)
        elif isinstance(msg, str):
            try:
                self._add_dic(data, json.loads(str(msg)))
            except:
                pass

    def _add_dic(self, data, dic):
        for k, v in dic.items():
            if isinstance(k, str) or isinstance(k, unicode):
                data[str(k)] = v

class FluentHandler(logging.Handler):
    '''
    Logging Handler for fluent.
    '''
    def __init__(self,
           tag,
           appname,
           host='localhost',
           port=24224,
           timeout=3.0,
           verbose=False):

        self.tag = tag
        self.sender = sender.FluentSender(tag,
                                          host=host, port=port,
                                          timeout=timeout, verbose=verbose)
        self.fmt = FluentRecordFormatter(appname)
        logging.Handler.__init__(self)

    def emit(self, record):
	if record.levelno < self.level: return
        data = self.fmt.format(record)
        self.sender.emit(None, data)

    def _close(self):
        self.sender._close()
