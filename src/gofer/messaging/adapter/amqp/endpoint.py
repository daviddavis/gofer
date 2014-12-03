# Copyright (c) 2013 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

from time import sleep
from logging import getLogger

from amqp import ChannelError

from gofer.messaging.adapter.model import BaseEndpoint
from gofer.messaging.adapter.amqp.connection import Connection, CONNECTION_EXCEPTIONS


log = getLogger(__name__)


# --- constants --------------------------------------------------------------


DELIVERY_TAG = 'delivery_tag'


# --- reconnect decorator ----------------------------------------------------


def reliable(fn):
    def _fn(endpoint, *args, **kwargs):
        while True:
            try:
                return fn(endpoint, *args, **kwargs)
            except CONNECTION_EXCEPTIONS:
                endpoint.close()
                sleep(3)
                endpoint.open()
    return _fn


# --- endpoint wrapper decorator ---------------------------------------------


def endpoint(fn):
    def _fn(url):
        _endpoint = Endpoint(url)
        _endpoint.open()
        try:
            return fn(_endpoint)
        finally:
            _endpoint.close()
    return _fn


# --- endpoint ---------------------------------------------------------------


class Endpoint(BaseEndpoint):
    """
    Base class for an AMQP endpoint.
    :ivar _connection: A connection.
    :type _connection: Connection
    :ivar _channel: An AMQP channel.
    :type _channel: amqp..Channel
    """

    def __init__(self, url):
        """
        :param url: The broker url.
        :type url: str
        """
        BaseEndpoint.__init__(self, url)
        self._connection = None
        self._channel = None

    def channel(self):
        """
        Get a channel for the open connection.
        :return: An open channel.
        :rtype: amqp.Channel
        """
        return self._channel

    def open(self):
        """
        Open and configure the endpoint.
        """
        connection = Connection(self.url)
        self._connection = connection.open()
        self._channel = connection.channel()

    @reliable
    def ack(self, message):
        """
        Ack the specified message.
        :param message: The message to acknowledge.
        :type message: amqp.Message
        """
        self._channel.basic_ack(message.delivery_info[DELIVERY_TAG])

    @reliable
    def reject(self, message, requeue=True):
        """
        Reject the specified message.
        :param message: The message to reject.
        :type message: amqp.Message
        :param requeue: Requeue the message or discard it.
        :type requeue: bool
        """
        self._channel.basic_reject(message.delivery_info[DELIVERY_TAG], requeue)

    def close(self):
        """
        Close the endpoint.
        """
        try:
            self._channel.close()
            self._connection.close()
        except (CONNECTION_EXCEPTIONS, ChannelError), e:
            log.exception(str(e))
