#!/usr/bin/env python

import base64
try:
    import eventlet
    from eventlet.green import urllib2
except ImportError:
    eventlet = None
    import urllib2
import getpass
import hashlib
try:
	import simplejson as json
except ImportError:
	import json
import sys
import time
import urllib
from pprint import pprint

def request(params):
    params['expire'] = int(time.time()) + 60
    if 'sig' in params: del params['sig']
    params['sig'] = hash_args(params, api_secret)

    base_url = 'http://mixpanel.com/api/2.0'
    request_url = '%s/%s?%s' % (base_url, 'engage', unicode_urlencode(params))

    request = urllib.urlopen(request_url)
    return json.load(request)

def unicode_urlencode(params):
    if isinstance(params, dict):
        params = params.items()
    for i, param in enumerate(params):
        if isinstance(param[1], list):
            params[i] = (param[0], json.dumps(param[1]),)

    return urllib.urlencode(
        [(k, isinstance(v, unicode) and v.encode('utf-8') or v) for k, v in params]
    )

def hash_args(args, api_secret):
    for a in args:
        if isinstance(args[a], list): args[a] = json.dumps(args[a])

    sorted_args = sorted(args.keys())
    if 'callback' in sorted_args:
        sorted_args.remove('callback')
    args_joined = ''.join([
        '%s=%s' % (isinstance(x, unicode) and x.encode('utf-8') or \
        x, isinstance(args[x], unicode) and \
        args[x].encode('utf-8') or args[x]) for x in sorted_args
    ])
    hash = hashlib.md5(args_joined)
    hash.update(api_secret)
    return hash.hexdigest()

def delete(user):
    distinct_id = user['$distinct_id']
    print '\tdeleting', distinct_id
    properties = {
        '$token': token,
        '$distinct_id': distinct_id,
        '$delete': True,
        '$ignore_alias':True
    }
    data = base64.b64encode(json.dumps(properties))
    host = 'api.mixpanel.com'
    params = {
        'data': data,
        'verbose': 1,
    }
    url = 'http://%s/%s/?%s' % (host, 'engage', urllib.urlencode(params))
    response = json.load(urllib2.urlopen(url))
    if response['status'] != 1:
        raise RuntimeError('%s\n%s' % (url, response))

current_user = getpass.getuser()
if len(sys.argv) == 4:
    api_key, api_secret, token = sys.argv[1:]
    print 'API key:', api_key
    print 'API secret:', api_secret
    print 'Token:', token
else:
    print 'Welome. This script will delete all the users in a project.'
    print "This is for real. You've been warned, %s." % current_user
    api_key = raw_input('API key: ')
    api_secret = raw_input('API secret: ')
    token =  raw_input('Token: ')
print

if eventlet:
    pool = eventlet.GreenPool(size=200)

params = {'api_key': api_key, 'selector', 'datetime(1386972989 - 2592000) > properties["$last_seen"] and properties["$plan"] = "Free"'}
while True: 
    print 'querying'
    response = request(params)
    try:
        if response['status'] != 'ok':
            raise RuntimeError('%r\n%s' % params, response)
    except KeyError:
        raise RuntimeError('%r\n%s' % params, response)
    if len(response['results']) == 0:
        break
    if 'page' not in params: # first iteration
        params['session_id'] = response['session_id']
        params['page'] = 0
    params['page'] += 1
    if eventlet:
        for user in response['results']:
            pool.spawn(delete, user)
        pool.waitall()
    else:
        map(delete, response['results'])

