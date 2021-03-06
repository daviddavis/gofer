# Copyright (c) 2014 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

from unittest import TestCase

from mock import patch, Mock

from gofer.devel import ipatch
from gofer import ThreadSingleton
from gofer.messaging.adapter.model import URL, Connector

with ipatch('proton'):
    from gofer.messaging.adapter.proton.connection import Connection


class TestConnection(TestCase):

    def setUp(self):
        ThreadSingleton.all().clear()

    def tearDown(self):
        ThreadSingleton.all().clear()

    @patch('gofer.messaging.adapter.model.SSL.validate')
    @patch('gofer.messaging.adapter.proton.connection.SSLDomain')
    def test_ssl_domain(self, ssl_domain, validate):
        ssl_domain.MODE_CLIENT = 0x01
        ssl_domain.VERIFY_PEER = 0x02
        ssl_domain.VERIFY_PEER_NAME = 0x03
        connector = Connector('amqps://localhost')
        connector.ssl.ca_certificate = 'ca'
        connector.ssl.client_certificate = 'client'
        connector.ssl.client_key = 'key'

        # test
        domain = Connection.ssl_domain(connector)

        # validation
        validate.assert_called_once_with()
        ssl_domain.assert_called_once_with(ssl_domain.MODE_CLIENT)
        domain.set_trusted_ca_db.assert_called_once_with(connector.ssl.ca_certificate)
        domain.set_credentials.assert_called_once_with(
            connector.ssl.client_certificate,
            connector.ssl.client_key, None)
        domain.set_peer_authentication.assert_called_once_with(ssl_domain.VERIFY_PEER)

    @patch('gofer.messaging.adapter.model.SSL.validate')
    @patch('gofer.messaging.adapter.proton.connection.SSLDomain')
    def test_ssl_domain_host_validation(self, ssl_domain, validate):
        ssl_domain.MODE_CLIENT = 0x01
        ssl_domain.VERIFY_PEER = 0x02
        ssl_domain.VERIFY_PEER_NAME = 0x03
        connector = Connector('amqps://localhost')
        connector.ssl.ca_certificate = 'ca'
        connector.ssl.client_certificate = 'client'
        connector.ssl.client_key = 'key'
        connector.ssl.host_validation = True

        # test
        domain = Connection.ssl_domain(connector)

        # validation
        validate.assert_called_once_with()
        ssl_domain.assert_called_once_with(ssl_domain.MODE_CLIENT)
        domain.set_trusted_ca_db.assert_called_once_with(connector.ssl.ca_certificate)
        domain.set_credentials.assert_called_once_with(
            connector.ssl.client_certificate,
            connector.ssl.client_key, None)
        domain.set_peer_authentication.assert_called_once_with(ssl_domain.VERIFY_PEER_NAME)

    def test_init(self):
        url = 'test-url'
        connection = Connection(url)
        self.assertEqual(connection.url, url)
        self.assertEqual(connection._impl, None)

    def test_is_open(self):
        connection = Connection('')
        self.assertFalse(connection.is_open())
        connection._impl = Mock()
        self.assertTrue(connection.is_open())

    @patch('gofer.messaging.adapter.proton.connection.Connector.find')
    @patch('gofer.messaging.adapter.proton.connection.BlockingConnection')
    @patch('gofer.messaging.adapter.proton.connection.Connection.ssl_domain')
    def test_open(self, ssl_domain, blocking, find):
        url = 'proton+amqps://localhost'
        find.return_value = Mock(url=URL(url), heartbeat=12)

        # test
        connection = Connection(url)
        connection.open()

        # validation
        canonical = URL(url).canonical
        find.assert_called_once_with(url)
        blocking.assert_called_once_with(
            canonical,
            heartbeat=find.return_value.heartbeat,
            ssl_domain=ssl_domain.return_value)

    @patch('gofer.messaging.adapter.proton.connection.BlockingConnection')
    def test_open_already(self, blocking):
        url = 'test-url'
        connection = Connection(url)
        connection.is_open = Mock(return_value=True)

        # test
        connection.open()

        # validation
        self.assertFalse(blocking.called)

    @patch('gofer.messaging.adapter.proton.connection.uuid4')
    def test_sender(self, uuid):
        url = 'test-url'
        address = 'test'
        uuid.return_value = '1234'
        connection = Connection(url)
        connection._impl = Mock()

        # test
        sender = connection.sender(address)

        # validation
        connection._impl.create_sender.assert_called_once_with(address, name=uuid.return_value)
        self.assertEqual(sender, connection._impl.create_sender.return_value)

    @patch('gofer.messaging.adapter.proton.connection.DynamicNodeProperties')
    @patch('gofer.messaging.adapter.proton.connection.uuid4')
    def test_receiver(self, uuid, properties):
        url = 'test-url'
        address = 'test'
        uuid.return_value = '1234'
        connection = Connection(url)
        connection._impl = Mock()

        # test
        receiver = connection.receiver(address)

        # validation
        connection._impl.create_receiver.assert_called_once_with(
            address, dynamic=False, name=uuid.return_value, options=None)
        self.assertEqual(receiver, connection._impl.create_receiver.return_value)
        self.assertFalse(properties.called)

    @patch('gofer.messaging.adapter.proton.connection.DynamicNodeProperties')
    @patch('gofer.messaging.adapter.proton.connection.uuid4')
    def test_dynamic_receiver(self, uuid, properties):
        url = 'test-url'
        address = 'test'
        uuid.return_value = '1234'
        connection = Connection(url)
        connection._impl = Mock()

        # test
        receiver = connection.receiver(address, dynamic=True)

        # validation
        properties.assert_called_once_with({'x-opt-qd.address': address})
        connection._impl.create_receiver.assert_called_once_with(
            None, dynamic=True, name=uuid.return_value, options=properties.return_value)
        self.assertEqual(receiver, connection._impl.create_receiver.return_value)

    def test_close(self):
        url = 'test-url'
        c = Connection(url)
        impl = Mock()
        c._impl = impl
        c.close()
        impl.close.assert_called_once_with()
        self.assertEqual(c._impl, None)

    def test_close_failed(self):
        url = 'test-url'
        c = Connection(url)
        impl = Mock()
        impl.close.side_effect = ValueError
        c._impl = impl
        c.close()
