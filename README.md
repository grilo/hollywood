# Hollywood

Yet another actor model implementation in python. This is mostly done as a
learning experience, but I'm having so much fun I'll probably keep maintaining it.

**Warning** This is not battle-tested, and very barebones. Use at your own peril!

Watch: https://www.youtube.com/watch?v=7erJ1DV_Tlo

Read: https://en.wikipedia.org/wiki/Actor_model

## Usage

An example containing an extremely basic HTTP server is
included.

To build your own actor which replies to http requests:

```python
import logging
import time

import hollywood.net.http


class MyResponseHandler(hollywood.actor.Threaded):

    def receive(self, request):
        response = hollywood.net.http.Response()
        response.content_type = 'text/plain'
        response.content = "<html><h1>Hello world!</h1></html>"
        request.send(response)
        return response

http_server = hollywood.System.new(hollywood.net.http.Server, MyResponseHandler)
http_server.tell(port=5000)

while True:
    logging.info("Actors alive: %i", hollywood.System.status() )
    time.sleep(2)
```

## Implementation

Everything that subclasses `hollywood.actor.Threaded` is automatically
registered as an actor. You just need to post messages and a single
actor processing those messages will be created and process them.

If you want more actors of a specific type, simply invoke the `.new` method
multiple times. Example:

```python
hollywood.System.new(hollywood.net.http.Server')
hollywood.System.new(hollywood.net.http.Server')
hollywood.System.new(hollywood.net.http.Server')
```

You could implement some sort of "AutoScaler" actor which spawns new actors
(and shuts them down) depending on the amount of incoming messages. It could
even be used to do round-robin to avoid flooding the same actor with messages
while others sit idly.

## Features/limitations

Implemented in python2.7, not tested in >=3.

There's no auto-scaling, no supervisors. Again, this is pretty bare bones.

Currently anything that can be passed as a function argument can be
passed as a message.

Only threaded actors are implemented (GIL limitations still apply).

Supports a whooping 300 requests per second. The same benchmark says that
`python -m SimpleHTTPServer` serves 2000.

## Contributing

Feel free to submit issues for new features, bugs, documentation.

PRs are also welcome.

## Alternatives

Please, consider one of the following:
  - https://github.com/jodal/pykka/
  - https://github.com/quantmind/pulsar
  - https://github.com/kquick/Thespian
