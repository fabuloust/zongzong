# -*- coding:utf-8 -*-

"""
@see redis.sentinel.SentinelConnectionPool
"""
from __future__ import absolute_import

import os
import random
import warnings
import weakref

from redis.connection import BlockingConnectionPool, UnixDomainSocketConnection, SSLConnection
from redis.sentinel import SentinelManagedConnection, MasterNotFoundError, SlaveNotFoundError


class CustomSentinelConnectionPool(BlockingConnectionPool):
    """
    Sentinel backed connection pool.

    If ``check_connection`` flag is set to True, SentinelManagedConnection
    sends a PING command right after establishing the connection.
    """

    def __init__(self, service_name, sentinel_manager, **kwargs):
        kwargs['connection_class'] = kwargs.get(
            'connection_class', SentinelManagedConnection)
        self.is_master = kwargs.pop('is_master', True)
        self.check_connection = kwargs.pop('check_connection', False)
        super(CustomSentinelConnectionPool, self).__init__(**kwargs)
        self.connection_kwargs['connection_pool'] = weakref.proxy(self)
        self.service_name = service_name
        self.sentinel_manager = sentinel_manager

    def __repr__(self):
        return "%s<service=%s(%s)" % (
            type(self).__name__,
            self.service_name,
            self.is_master and 'master' or 'slave',
        )

    def reset(self):
        super(CustomSentinelConnectionPool, self).reset()
        self.master_address = None
        self.slave_rr_counter = None

    def get_master_address(self):
        master_address = self.sentinel_manager.discover_master(
            self.service_name)
        if self.is_master:
            if self.master_address is None:
                self.master_address = master_address
            elif master_address != self.master_address:
                # Master address changed, disconnect all clients in this pool
                self.disconnect()
                self.master_address = master_address  # 主从切换后，影响一次。
        return master_address

    def rotate_slaves(self):
        "Round-robin slave balancer"
        slaves = self.sentinel_manager.discover_slaves(self.service_name)
        if slaves:
            if self.slave_rr_counter is None:
                self.slave_rr_counter = random.randint(0, len(slaves) - 1)
            for _ in range(len(slaves)):
                self.slave_rr_counter = (self.slave_rr_counter + 1) % len(slaves)
                slave = slaves[self.slave_rr_counter]
                yield slave
        # Fallback to the master connection
        try:
            yield self.get_master_address()
        except MasterNotFoundError:
            pass
        raise SlaveNotFoundError('No slave found for %r' % self.service_name)

    def _checkpid(self):
        if self.pid != os.getpid():
            self.disconnect()
            self.reset()
            self.__init__(self.service_name, self.sentinel_manager,
                          connection_class=self.connection_class,
                          max_connections=self.max_connections,
                          **self.connection_kwargs)


def create_block_redis_connection_pool(
        host='localhost', port=6379,
        db=0, password=None, socket_timeout=None,
        socket_connect_timeout=None,
        socket_keepalive=None, socket_keepalive_options=None,
        unix_socket_path=None,
        encoding='utf-8', encoding_errors='strict',
        charset=None, errors=None,
        decode_responses=False, retry_on_timeout=False,
        ssl=False, ssl_keyfile=None, ssl_certfile=None,
        ssl_cert_reqs=None, ssl_ca_certs=None,
        max_connections=None):
    """
    StrictRedis默认使用的连接池非线程安全
    创建一个线程安全的连接池
      max_connections: 为None时，默认为50, @see BlockingConnectionPool
    """
    # copied from pyredis.StrictRedis __init__
    # but use BlockingConnectionPool instead of ConnectionPool
    if charset is not None:
        warnings.warn(DeprecationWarning(
            '"charset" is deprecated. Use "encoding" instead'))
        encoding = charset
    if errors is not None:
        warnings.warn(DeprecationWarning(
            '"errors" is deprecated. Use "encoding_errors" instead'))
        encoding_errors = errors

    kwargs = {
        'db': db,
        'password': password,
        'socket_timeout': socket_timeout,
        'encoding': encoding,
        'encoding_errors': encoding_errors,
        'decode_responses': decode_responses,
        'retry_on_timeout': retry_on_timeout
    }
    # based on input, setup appropriate connection args
    if unix_socket_path is not None:
        kwargs.update({
            'path': unix_socket_path,
            'connection_class': UnixDomainSocketConnection
        })
    else:
        # TCP specific options
        kwargs.update({
            'host': host,
            'port': port,
            'socket_connect_timeout': socket_connect_timeout,
            'socket_keepalive': socket_keepalive,
            'socket_keepalive_options': socket_keepalive_options,
        })

        if ssl:
            kwargs.update({
                'connection_class': SSLConnection,
                'ssl_keyfile': ssl_keyfile,
                'ssl_certfile': ssl_certfile,
                'ssl_cert_reqs': ssl_cert_reqs,
                'ssl_ca_certs': ssl_ca_certs,
            })
    if max_connections:
        kwargs["max_connections"] = max_connections
    connection_pool = BlockingConnectionPool(**kwargs)
    return connection_pool

