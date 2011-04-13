#
# Copyright (c) 2010 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.
#

"""
Agent base classes.
"""

from gofer.messaging import *
from gofer.messaging.stub import Stub
from gofer.messaging.mock import Factory
from gofer.messaging.decorators import Remote
from gofer.messaging.dispatcher import Dispatcher, ConcurrentDispatcher
from gofer.messaging.window import Window
from logging import getLogger

log = getLogger(__name__)



class Agent:
    """
    The agent base provides a dispatcher and automatic
    registration of methods based on decorators.
    @ivar consumer: A qpid consumer.
    @type consumer: L{gofer.messaging.Consumer}
    """

    def __init__(self, consumer, threads=1):
        """
        Construct the L{Dispatcher} using the specified
        AMQP I{consumer} and I{start} the AMQP consumer.
        @param consumer: A qpid consumer.
        @type consumer: L{gofer.messaging.Consumer}
        @param threads: The number of thread in the dispatcher.
        @type threads: int
        """
        assert(threads > 0)
        if threads > 1:
            dispatcher = ConcurrentDispatcher()
        else:
            dispatcher = Dispatcher()
        remote = Remote()
        dispatcher.register(*remote.collated())
        consumer.start(dispatcher)
        self.consumer = consumer

    def close(self):
        """
        Close and release all resources.
        """
        self.consumer.close()
        
        
class Container:
    """
    The stub container
    @ivar __id: The peer ID.
    @type __id: str
    @ivar __producer: An AMQP producer.
    @type __producer: L{gofer.messaging.producer.Producer}
    @ivar __options: Container options.
    @type __options: L{Options}
    """

    def __init__(self, uuid, producer, **options):
        """
        @param uuid: The peer ID.
        @type uuid: str
        @param producer: An AMQP producer.
        @type producer: L{gofer.messaging.producer.Producer}
        @param options: keyword options.
        @type options: dict
        """
        self.__id = uuid
        self.__producer = producer
        self.__options = Options(window=Window())
        self.__options.update(options)

    def __destination(self):
        """
        Get the stub destination(s).
        @return: Either a queue destination or a list of queues.
        @rtype: list
        """
        if isinstance(self.__id, (list,tuple)):
            queues = []
            for d in self.__id:
                queues.append(Queue(d))
            return queues
        else:
            return Queue(self.__id)
    
    def __getattr__(self, name):
        """
        Get a stub by name.
        @param name: The name of a stub class.
        @type name: str
        @return: A stub object.
        @rtype: L{Stub}
        """
        stub = Factory.stub(name)
        if stub:
            return stub
        return Stub.stub(
            name,
            self.__producer,
            self.__destination(),
            self.__options)

    def __str__(self):
        return '{%s} opt:%s' % (self.__id, str(self.__options))
    
    def __repr__(self):
        return str(self)
