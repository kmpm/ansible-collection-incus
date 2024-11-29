from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
from ansible.module_utils.six.moves.urllib.parse import urlparse, parse_qs


fixturedir = os.path.join(os.path.dirname(__file__), 'fixtures')
status_messages = {
    0: '',
    200: 'Success',
}

error_messages = {
    0: '',
    404: 'Not Found',
    500: 'Internal Server Error',
    501: 'Not Implemented',
}


def load_fixture(name):
    with open(os.path.join(fixturedir, name)) as f:
        return json.load(f)


def generate_response(**kwargs):
    resp = {
        'type': 'sync',
        'status': '',
        'status_code': 0,
        'operation': '',
        'error_code': 0,
        'error': '',
        'metadata': None
    }
    for k, v in kwargs.items():
        if k in resp:
            resp[k] = v

    resp['status'] = status_messages.get(resp['status_code'], '')
    if resp['error_code']:
        resp['error'] = error_messages.get(resp['error_code'], '')
        resp['type'] = 'error'

    return resp


class MockClient:
    instances = {}
    counter = 0
    request = {}

    def _response(self, value):
        stringval = json.dumps(value)
        print("response", dict(requst=self.request, response=stringval))
        return stringval

    def _instances_api(self, method, segments, queryargs, data):
        name = segments[0] if len(segments) > 0 else None
        if not name:
            if method == 'GET':
                return json.dumps([])
            elif method == 'POST':
                # create instance
                name = data['name']
                metadata = load_fixture('get_instance.json')['metadata']
                metadata['name'] = name
                metadata['project'] = queryargs.get('project', ['default'])[0]
                self.instances[name] = metadata
                resp = load_fixture('post_instance.json')
                self.counter += 1
                resp['metadata']['id'] = '1337-42-%d' % self.counter
                resp['metadata']['name'] = metadata['name']
                resp['metadata']['project'] = metadata['project']
                # print("creates instance", name, resp['metadata'])
                return self._response(resp)

        segments = segments[1:]
        if segments and segments[0] == 'state':
            segments = segments[1:]
            if method == 'GET':
                # return named instance state if any
                if name in self.instances:
                    resp = load_fixture('get_instance_state.json')
                    metadata = self.instances[name]
                    resp['metadata'] = self.instances[name]['state']
                    return self._response(resp)
                else:
                    return json.dumps(generate_response(error_code=404))
            elif method == 'PUT':
                # update state
                if name in self.instances:
                    resp = load_fixture('put_instance_state.json')
                    self.instances[name]['status'] = "Running"
                    self.instances[name]['status_code'] = "103"

                    return self._response(resp)
                else:
                    return self._response(generate_response(error_code=404))
        else:
            if method == 'GET':
                # return named instance if any
                if name in self.instances:
                    resp = generate_response(status_code=200)
                    resp['metadata'] = self.instances[name]
                    return self._response(resp)
                else:
                    return self._response(generate_response(error_code=404))

        raise Exception('instance action: %s %r' % (method, segments,))

    def execute(self, client, *args, **kwargs):
        # if client.debug:
        client.debug = True
        client.logs.append(args)
        method = args[2]
        querypath = args[3]
        # extract queryargs from querypath
        p = urlparse(querypath)
        queryargs = parse_qs(p.query)
        data = None
        for i, arg in enumerate(args):
            if arg == '--data':
                data = json.loads(args[i + 1])

        self.request = dict(path=querypath, data=data)
        # extract segments from querypath
        segments = p.path.split('/')
        # remove empty first segment
        segments = segments[1:]
        # is the first segment '1.0'?
        if segments[0] != '1.0':
            raise Exception('Unknown version: %s' % segments)

        # remove version segment
        segments = segments[1:]

        if segments[0] == 'instances':
            return self._instances_api(method, segments[1:], queryargs, data)

        else:
            print("log", client.logs)
            raise Exception('Unknown method or querypath: %s %s' % (method, querypath,))
