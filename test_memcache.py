#!/usr/bin/env python
# script to test memcached instance

from pymemcache.client import base

client = base.Client(('localhost', 11211))

client.set('greeting', 'hi there')

greeting = client.get('greeting')

print(greeting)