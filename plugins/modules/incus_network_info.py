#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2024, Peter Magnusson <me@kmpm.se>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: incus_network_info
author: "Peter Magnusson (@kmpm)"
short_description: Get information about incus networks
description:
  - Get information about incus networks
extends_documentation_fragment:
  - kmpm.incus.attributes
  - kmpm.incus.attributes.info_module
options:
    name:
        description:
            - Name of the network. If empty all networks will be returned.
        type: str
        required: false
    remote:
        description: The remote to use for the Incus CLI.
        type: str
        default: local
    project:
        description:
            - Project to get network information from
        type: str
        default: default
    target:
        description:
          - For cluster deployments.
        type: str
        required: false
'''
EXAMPLES = '''
- host: localhost
  connection: local
  tasks:
    - name: Get all networks
      kmpm.incus.incus_network_info:
        project: default
        register: networks

'''

RETURN = r'''
networks_info:
    description: A list of networks
    type: list
    elements: dict
    returned: success when O(name) is not set
    sample:
        - name: "net1"
          type: "bridge"
          config: {}
          project: "default"
          description: "My network"

network_info:
    description: Information about a single network
    type: dict
    returned: success when O(name) is set
    sample:
        name: "net1"
        type: "bridge"
        config: {}
        project: "default"
        description: "My network"

'''


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kmpm.incus.plugins.module_utils.incuscli import IncusClient, IncusClientException

NETWORK_FIELDS = ['name', 'type', 'config', 'project', 'description', 'managed', 'status', 'locations']


class IncusNetworkInfo(object):
    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.project = module.params['project']
        self.target = module.params['target']
        self.remote = module.params['remote']

        self.client = IncusClient(project=self.project, target=self.target, remote=self.remote)
        self.api_endpoint = '/1.0/networks'
        self.logs = []

    def _read_network(self, data):
        out = {}
        for field in data:
            if field in NETWORK_FIELDS:
                out[field] = data[field]

        return out

    def _get_networks(self):
        response = self.client.query_raw('GET', self.api_endpoint)
        if response.get('type') == 'error':
            self.logs.append(response.get('error'))
            return []

        data = []
        urls = response.get('metadata', [])
        for url in urls:
            if url in [self.api_endpoint + '/lo']:
                continue
            response = self.client.query_raw('GET', url, ok_errors=[404])
            if response.get('type') == 'error':
                self.logs.append(response.get('error'))
                continue
            network = response.get('metadata', {})
            if network and not network['name'] in ['lo',]:
                data.append(self._read_network(network))
        return data

    def _get_network(self):
        url = '{0}/{1}'.format(self.api_endpoint, self.name)
        response = self.client.query_raw('GET', url, ok_errors=[404])
        if response.get('type') == 'error':
            self.logs.append(response.get('error'))
            return {}
        return self._read_network(response.get('metadata', {}))

    def run(self):
        result = dict(changed=False, )
        try:
            if self.name:
                result['network_info'] = self._get_network()
            else:
                result['networks_info'] = self._get_networks()

            self.module.exit_json(**result)

        except IncusClientException as e:
            self.module.fail_json(msg=e.msg, **e.kwargs)


def main():
    '''Ansible Main module.'''

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=False),
            remote=dict(type='str', default='local'),
            project=dict(type='str', default='default'),
            target=dict(type='str', required=False),
        ),
        supports_check_mode=True
    )

    info = IncusNetworkInfo(module)
    info.run()


if __name__ == '__main__':
    main()
