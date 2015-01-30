Release Notes
=============

gofer 1.4
^^^^^^^^^

Here is a summary of 1.0 changes:

- Support for multiple *transports* was added.
- Message authentication added.
- The *accepted* status reply was added.
- The *watchdog* as removed.
- An ISO 8601 timestamp is included in all reply messages.

gofer 2.0
^^^^^^^^^

The 2.0 major release and contains API changes, minor message format changes
and the removal of deprecated functionality. The goal of this release was to overhaul
and streamline may major component and flows. This release also contains hundreds of new unit
integration and unit tests as part of a major effort to reach 100% test coverage.


Overhauled:

- The agent thread pool was replaced with *Queue* based approach.
- Support for multiple messaging libraries. Standard messaging adapter model that
  uses delegation pattern instead of python meta-classes. Much better.


Concept changes
---------------

- The *transport* concept was replaced with *messaging adapters*. Each *adapter* implements
  an interface defined in the adapter model and provides integration with 3rd part AMQP
  messaging libraries. The *transport* option and descriptor property replaced with
  rich protocol handler support in the URL. See documented URL.

- All options are only supported when creating the agent proxy. They are no longer supported
  when constructing the stub. This semantic is not reserved for passing arguments to the remote
  object (class) constructor.

- The agent *uuid* is being phased out. RMI calls are routed to the agent based on the
  queue on which it was received. This term is being replaced by more AMQP related
  terms and concepts. A route has the format of: *exchange*/*queue* or *queue*.

- Support for agent broadcast was removed. This feature was deemed as not useful since
  most applications do not track requests using the serial number. Also, this can be
  easily implemented by the caller. Removed to make code paths and the API simpler.

API changes
-----------

There are API changes that affect both RMI calling (proxy) and the Plugin object exposed
to agent plugins. Proxy changes pertain to the options passed to the *Agent* class and the
*Stubs* created.

The *Agent* constructor changed from: Agent(uuid, **options) to: Agent(url, route, **options).

Example (adapter = qpid)::

 url = qpid+amqp://localhost


Option changes:

- *async* - Removed.
- *wait* - Added and indicates how long the caller is blocked on calls.
- *timeout* - Replaced by *ttl*.
- *ttl* - Added and replaces *timeout*. Strictly applies to request (and message) TTL.
- *ctag* - Replaced by *reply*.
- *reply* - Replaces *ctag* and is an AMQP route that specifies where RMI replies are sent.
- *any* - Removed and replaced by *data*.
- *data* - User defined data that is round-tripped back to the caller. Replaces *any*.
- *transport* - Replaced with rich protocol handlers supported by the URL.

Plugin (class) changes
----------------------

All accessor methods replaced with *@property* and appear as attributes.

Here are a few major methods affected:

- enabled()
- get_uuid()
- get_url()
- get_cfg()


gofer 2.1
^^^^^^^^^

Not Released.

gofer 2.2
^^^^^^^^^

Not Released.

gofer 2.3
^^^^^^^^^

Notes:

- Support for custom AMQP exchanges added. This includes an additional *exchange* option
  passed by callers to indicate the exchange to be used for temporary queues used for
  synchronous replies. For plugins, the descriptor was augmented to support an *exchange*
  property in the [messaging] section.

gofer 2.4
^^^^^^^^^

Notes:

 - AMQP Message durability fixed in python-amqp adapter.

 - Added support for plugin descriptor properties that specifies the level to which
   the agent manages the broker model. Specifically, how the agent manages its
   request queue. The ``[messaging]`` *exchange* property was replace by support in the
   new [model] section documented below. See: descriptor documentation for details.

 - Thread pool distribution fixed so that idle worker threads are selected when available.

 - The python-amqplib AMQP library is no longer supported. It was redundant to support
   for python-amqp which is better maintained and widely available. This means that the
   python-gofer-amqplib package is no longer provided. Further that, AMQP-0-8 is no longer
   supported. This functionality can be resurrected on community request.

 - The *amqp* adapter (python-amqp) updated to use EPOLL and basic_consume() instead of
   using dynamic polling and basic_get().

 - By default, the proxy (caller) will no longer declare the agent queue. Since the *route*
   really specifies AMQP routing (exchange/queue), gofer cannot assume the queue name
   or properties. The agent declaration and binding is the responsibility of the agent
   or the (caller) application.
   
 - The *qpid* adapter enables qpid heartbeat option on connections.

Added ``[model]`` section with the following properties:

- *managed* - Defines level of broker model management.
- *queue* - The name of the request queue.
- *exchange* - An (optional) exchange. The exchange is not declared/deleted.