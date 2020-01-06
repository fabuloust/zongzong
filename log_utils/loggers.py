# -*- coding: utf-8 -*-
"""
定义各 logger
如果是Django工程，只需要在settings中`from cy_common.logging.config import LOGGING`
如果是非Django工程，需要执行`cy_common.logging.config.configure_logging()`
"""
from __future__ import absolute_import

import logging

error_logger = logging.getLogger('django.request')
exception_logger = logging.getLogger('exception_logger')
ticker_logger = logging.getLogger('ticker_logger')
push_logger = logging.getLogger('push_logger')
elapsed_logger = logging.getLogger('elapsed_logger')
info_logger = logging.getLogger('info_logger')
action_logger = logging.getLogger('action_logger')
problem_action_logger = logging.getLogger('problem_action_logger')
search_logger = logging.getLogger('search_logger')
celery_logger = logging.getLogger('celery_logger')
rpc_server_logger = logging.getLogger('rpc_server')
rpc_client_logger = logging.getLogger('rpc_client')
msg_bus_logger = logging.getLogger('msg_bus')
http_requests_logger = logging.getLogger('http_requests')
