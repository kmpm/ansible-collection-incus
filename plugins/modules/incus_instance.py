#!/usr/bin/python
# -*- coding: utf-8 -*-
# Based on community.general.lxd_container.py by (c) 2016, Hiroaki Nakamura <hnakamur@gmail.com>
# (c) 2024, Peter Magnusson <me@kmpm.se>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = '''
---
module: incus_instance
short_description: Manage Incus instances
description:
  - Management of Incus containers and virtual machines.
author: "Hiroaki Nakamura (@hnakamur)"
extends_documentation_fragment:
  - kmpm.incus.attributes
attributes:
    check_mode:
        support: full
    diff_mode:
        support: full
options:
    name:
        description:
          - Name of an instance.
        type: str
        required: true
    remote:
        description: The remote to use for the Incus CLI.
        type: str
        default: local
    description:
        description:
            - Description of the instance
        type: str
        required: false
    project:
        description:
          - 'Project of an instance.
            See U(https://linuxcontainers.org/incus/docs/main/projects/).'
        required: false
        type: str
        default: default
    architecture:
        description:
          - 'The architecture for the instance (for example V(x86_64) or V(i686)).
            See U(https://linuxcontainers.org/incus/docs/main/rest-api-spec/#/instances/instances_get).'
        type: str
        required: false
    config:
        description:
          - 'The config for the instance (for example V({"limits.cpu": "2"})).
            See U(https://linuxcontainers.org/incus/docs/main/rest-api-spec/#/instances/instance_get).'
          - If the instance already exists and its "config" values in metadata
            obtained from the Incus API U(https://linuxcontainers.org/incus/docs/main/rest-api-spec/#/instances/instance_get)
            are different, then this module tries to apply the configurations
            U(https://linuxcontainers.org/incus/docs/main/rest-api-spec/#/instances/instance_put).
          - The keys starting with C(volatile.) are ignored for this comparison when O(ignore_volatile_options=true).
        type: dict
        required: false
    ignore_volatile_options:
        description:
          - If set to V(true), options starting with C(volatile.) are ignored. As a result,
            they are reapplied for each execution.
          - This default behavior can be changed by setting this option to V(false).
          - The default value changed from V(true) to V(false) in kmpm.incus 6.0.0.
        type: bool
        required: false
        default: false
    profiles:
        description:
          - Profile to be used by the instance.
        type: list
        elements: str
    devices:
        description:
          - 'The devices for the instance
            (for example V({ "rootfs": { "path": "/dev/kvm", "type": "unix-char" }})).
            See U(https://linuxcontainers.org/incus/docs/main/rest-api-spec/#/instances/instance_get).'
        type: dict
        required: false
    ephemeral:
        description:
          - Whether or not the instance is ephemeral (for example V(true) or V(false)).
            See U(https://linuxcontainers.org/incus/docs/main/rest-api-spec/#/instances/instance_get).
        required: false
        type: bool
    source:
        description:
          - 'The source for the instance
            (for example V({ "type": "image", "mode": "pull", "server": "https://images.linuxcontainers.org",
            "protocol": "lxd", "alias": "ubuntu/xenial/amd64" })).'
          - 'See U(https://linuxcontainers.org/incus/docs/main/rest-api/) for complete API documentation.'
          - 'Note that C(protocol) accepts two choices: V(lxd) or V(simplestreams).'
        required: false
        type: dict
    state:
        choices:
          - started
          - stopped
          - restarted
          - absent
          - frozen
        description:
          - Define the state of an instance.
        required: false
        default: started
        type: str
    target:
        description:
          - For cluster deployments. Will attempt to create an instance on a target node.
            If the instance exists elsewhere in a cluster, then it will not be replaced or moved.
            The name should respond to same name of the node you see in C(incus cluster list).
        type: str
        required: false
    timeout:
        description:
          - A timeout for changing the state of the instance.
          - This is also used as a timeout for waiting until IPv4 addresses
            are set to the all network interfaces in the instance after
            starting or restarting.
        required: false
        default: 30
        type: int
    type:
        description:
          - Instance type can be either V(virtual-machine) or V(container).
        required: false
        default: container
        choices:
          - container
          - virtual-machine
        type: str
    wait_for_ipv4_addresses:
        description:
          - If this is V(true), the C(incus_instance) waits until IPv4 addresses
            are set to the all network interfaces in the instance after
            starting or restarting.
        required: false
        default: false
        type: bool
    wait_for_container:
        description:
            - If set to V(true), the tasks will wait till the task reports a
              success status when performing container operations.
        default: false
        type: bool
    force_stop:
        description:
          - If this is V(true), the C(incus_instance) forces to stop the instance
            when it stops or restarts the instance.
        required: false
        default: false
        type: bool
notes:
  - Instances can be a container or a virtual machine, both of them must have unique name. If you attempt to create an instance
    with a name that already existed in the users namespace the module will
    simply return as "unchanged".
  - There are two ways to run commands inside a container or virtual machine, using the command
    module or using the ansible incus connection plugin bundled in Ansible >=
    2.1, the later requires python to be installed in the instance which can
    be done with the command module.
  - You can copy a file from the host to the instance
    with the Ansible M(ansible.builtin.copy) and M(ansible.builtin.template) module
    and the P(kmpm.incus.incus#connection) connection plugin.
    See the example below.
  - You can copy a file in the created instance to the localhost
    with C(command=incus file pull instance_name/dir/filename filename).
    See the first example below.
'''

EXAMPLES = '''
# An example for creating a Debian container and install python
- hosts: localhost
  connection: local
  tasks:
    - name: Create a started container
      kmpm.incus.incus_instance:
        name: mycontainer
        ignore_volatile_options: true
        state: started
        source:
          type: image
          mode: pull
          server: https://images.linuxcontainers.org
          protocol: simplestreams
          alias: debian/12
        profiles: ["default"]
        wait_for_ipv4_addresses: true
        timeout: 600

    - name: Check python is installed in container
      delegate_to: mycontainer
      ansible.builtin.raw: dpkg -s python
      register: python_install_check
      failed_when: python_install_check.rc not in [0, 1]
      changed_when: false

    - name: Install python in container
      delegate_to: mycontainer
      ansible.builtin.raw: apt-get install -y python
      when: python_install_check.rc == 1

# An example for creating container in project other than default
- hosts: localhost
  connection: local
  tasks:
    - name: Create a started container in project mytestproject
      kmpm.incus.incus_instance:
        name: mycontainer
        project: mytestproject
        ignore_volatile_options: true
        state: started
        source:
          protocol: simplestreams
          type: image
          mode: pull
          server: https://images.linuxcontainers.org
          alias: ubuntu/20.04/cloud
        profiles: ["default"]
        wait_for_ipv4_addresses: true
        timeout: 600

# An example for deleting a container
- hosts: localhost
  connection: local
  tasks:
    - name: Delete a container
      kmpm.incus.incus_instance:
        name: mycontainer
        state: absent
        type: container

# An example for restarting a container
- hosts: localhost
  connection: local
  tasks:
    - name: Restart a container
      kmpm.incus.incus_instance:
        name: mycontainer
        state: restarted
        type: container

# An example for restarting a container using https to connect to the Incus server
- hosts: localhost
  connection: local
  tasks:
    - name: Restart a container
      kmpm.incus.incus_instance:
        url: https://127.0.0.1:8443
        # These client_cert and client_key values are equal to the default values.
        #client_cert: "{{ lookup('env', 'HOME') }}/.config/incus/client.crt"
        #client_key: "{{ lookup('env', 'HOME') }}/.config/incus/client.key"
        name: mycontainer
        state: restarted

# Note your container must be in the inventory for the below example.
#
# [containers]
# mycontainer ansible_connection=incus
#
- hosts:
    - mycontainer
  tasks:
    - name: Copy /etc/hosts in the created container to localhost with name "mycontainer-hosts"
      ansible.builtin.fetch:
        src: /etc/hosts
        dest: /tmp/mycontainer-hosts
        flat: true

# An example for Incus cluster deployments. This example will create two new container on specific
# nodes - 'node01' and 'node02'. In 'target:', 'node01' and 'node02' are names of Incus cluster
# members that Incus cluster recognizes, not ansible inventory names, see: 'incus cluster list'.
# Incus API calls can be made to any Incus member, in this example, we send API requests to
#'node01.example.com', which matches ansible inventory name.
- hosts: node01.example.com
  tasks:
    - name: Create Incus container
      kmpm.incus.incus_instance:
        name: new-container-1
        ignore_volatile_options: true
        state: started
        source:
          type: image
          mode: pull
          alias: ubuntu/xenial/amd64
        target: node01

    - name: Create container on another node
      kmpm.incus.incus_instance:
        name: new-container-2
        ignore_volatile_options: true
        state: started
        source:
          type: image
          mode: pull
          alias: ubuntu/xenial/amd64
        target: node02

# An example for creating a virtual machine
- hosts: localhost
  connection: local
  tasks:
    - name: Create container on another node
      kmpm.incus.incus_instance:
        name: new-vm-1
        type: vm
        state: started
        ignore_volatile_options: true
        wait_for_ipv4_addresses: true
        profiles: ["default"]
        source:
          protocol: simplestreams
          type: image
          mode: pull
          server: https://images.linuxcontainers.org
          alias: debian/11
        timeout: 600
'''

RETURN = '''
addresses:
  description: Mapping from the network device name to a list of IPv4 addresses in the instance.
  returned: when state is started or restarted
  type: dict
  sample: {"eth0": ["10.155.92.191"]}
old_state:
  description: The old state of the instance.
  returned: when state is started or restarted
  type: str
  sample: "stopped"
logs:
  description: The logs of requests and responses.
  returned: when ansible-playbook is invoked with -vvvv.
  type: list
  sample: "(too long to be placed here)"
actions:
  description: List of actions performed for the instance.
  returned: success
  type: list
  sample: ["create", "start"]
'''
import copy
import datetime
import time

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kmpm.incus.plugins.module_utils.incuscli import (
    IncusClient, IncusClientException)

# INCUS_ANSIBLE_STATES is a map of states that contain values of methods used
# when a particular state is evoked.
INCUS_ANSIBLE_STATES = {
    'started': '_started',
    'stopped': '_stopped',
    'restarted': '_restarted',
    'absent': '_destroyed',
    'frozen': '_frozen',
}

# ANSIBLE_INCUS_STATES is a map of states of incus containers to the Ansible
# incus_container module state parameter value.
ANSIBLE_INCUS_STATES = {
    'Running': 'started',
    'Stopped': 'stopped',
    'Frozen': 'frozen',
}

# CONFIG_PARAMS is a list of config attribute names.
CONFIG_PARAMS = [
    'name', 'description', 'architecture', 'config', 'devices', 'ephemeral', 'profiles', 'source', 'type'
]

# CONFIG_CREATION_PARAMS is a list of attribute names that are only applied
# on instance creation.
CONFIG_CREATION_PARAMS = ['source', 'type']


class IncusInstanceManagement(object):
    def __init__(self, module):
        """Management of Incus containers via Ansible.

        :param module: Processed Ansible Module.
        :type module: ``object``
        """
        self.module = module
        self.name = self.module.params['name']
        self.project = self.module.params['project']
        self.description = self.module.params['description']
        self.remote = self.module.params['remote']
        self._build_config()

        self.state = self.module.params['state']
        self.api_endpoint = '/1.0/instances'
        self.timeout = self.module.params['timeout']
        self.wait_for_ipv4_addresses = self.module.params['wait_for_ipv4_addresses']
        self.force_stop = self.module.params['force_stop']
        self.addresses = None
        self.target = self.module.params['target']
        self.wait_for_container = self.module.params['wait_for_container']

        self.type = self.module.params['type']

        self.debug = self.module._verbosity >= 3

        try:
            self.client = IncusClient(
                project=self.project,
                remote=self.remote,
                debug=self.debug
            )
        except IncusClientException as e:
            self.module.fail_json(msg=e.msg)

        self.actions = []
        self.diff = {'before': {}, 'after': {}}
        self.old_instance = {}
        self.old_sections = {}

    def _build_config(self):
        self.config = {}
        for attr in CONFIG_PARAMS:
            param_val = self.module.params.get(attr, None)
            if param_val is not None:
                self.config[attr] = param_val

    def _get_instance_json(self):
        url = '{0}/{1}'.format(self.api_endpoint, self.name)
        try:
            return self.client.query_raw('GET', url)
        except IncusClientException as ex:
            return {'type': 'error', 'error': ex.msg}

    def _get_instance_state_json(self):
        url = '{0}/{1}/state'.format(self.api_endpoint, self.name)
        return self.client.query_raw('GET', url, ok_errors=[404])

    @staticmethod
    def _instance_json_to_module_state(resp_json):
        if resp_json['type'] == 'error':
            return 'absent'
        return ANSIBLE_INCUS_STATES[resp_json['metadata']['status']]

    def _change_state(self, action, force_stop=False):
        url = '{0}/{1}/state'.format(self.api_endpoint, self.name)
        payload = {'action': action, 'timeout': self.timeout}
        if force_stop:
            payload['force'] = True
        if not self.module.check_mode:
            return self.client.query_raw('PUT', url, payload=payload)

    def _create_instance(self):
        url = self.api_endpoint
        url_params = dict()
        if self.target:
            url_params['target'] = self.target
        if self.project:
            url_params['project'] = self.project

        config = self.config.copy()
        config['name'] = self.name
        if self.type not in self.api_endpoint:
            config['type'] = self.type
        if not self.module.check_mode:
            # self.client.do('POST', url, config, wait_for_container=self.wait_for_container)
            self.client.query_raw('POST', url, payload=config, url_params=url_params)
        self.actions.append('create')

    def _start_instance(self):
        self._change_state('start')
        self.actions.append('start')

    def _stop_instance(self):
        self._change_state('stop', self.force_stop)
        self.actions.append('stop')

    def _restart_instance(self):
        self._change_state('restart', self.force_stop)
        self.actions.append('restart')

    def _delete_instance(self):
        url = '{0}/{1}'.format(self.api_endpoint, self.name)
        if not self.module.check_mode:
            self.client.query_raw('DELETE', url)
        self.actions.append('delete')

    def _freeze_instance(self):
        self._change_state('freeze')
        self.actions.append('freeze')

    def _unfreeze_instance(self):
        self._change_state('unfreeze')
        self.actions.append('unfreeze')

    def _instance_ipv4_addresses(self, ignore_devices=None):
        ignore_devices = ['lo'] if ignore_devices is None else ignore_devices
        data = (self._get_instance_state_json() or {}).get('metadata', None) or {}
        network = dict((k, v) for k, v in (data.get('network', None) or {}).items() if k not in ignore_devices)
        addresses = dict((k, [a['address'] for a in v['addresses'] if a['family'] == 'inet']) for k, v in network.items())
        return addresses

    @staticmethod
    def _has_all_ipv4_addresses(addresses):
        return len(addresses) > 0 and all(len(v) > 0 for v in addresses.values())

    def _get_addresses(self):
        try:
            due = datetime.datetime.now() + datetime.timedelta(seconds=self.timeout)
            while datetime.datetime.now() < due:
                time.sleep(1)
                addresses = self._instance_ipv4_addresses()
                if self._has_all_ipv4_addresses(addresses) or self.module.check_mode:
                    self.addresses = addresses
                    return
        except IncusClientException as e:
            e.msg = 'timeout for getting IPv4 addresses'
            raise

    def _started(self):
        if self.old_state == 'absent':
            self._create_instance()
            self._start_instance()
        else:
            if self.old_state == 'frozen':
                self._unfreeze_instance()
            elif self.old_state == 'stopped':
                self._start_instance()
            if self._needs_to_apply_instance_configs():
                self._apply_instance_configs()
        if self.wait_for_ipv4_addresses:
            self._get_addresses()

    def _stopped(self):
        if self.old_state == 'absent':
            self._create_instance()
        else:
            if self.old_state == 'stopped':
                if self._needs_to_apply_instance_configs():
                    self._start_instance()
                    self._apply_instance_configs()
                    self._stop_instance()
            else:
                if self.old_state == 'frozen':
                    self._unfreeze_instance()
                if self._needs_to_apply_instance_configs():
                    self._apply_instance_configs()
                self._stop_instance()

    def _restarted(self):
        if self.old_state == 'absent':
            self._create_instance()
            self._start_instance()
        else:
            if self.old_state == 'frozen':
                self._unfreeze_instance()
            if self._needs_to_apply_instance_configs():
                self._apply_instance_configs()
            self._restart_instance()
        if self.wait_for_ipv4_addresses:
            self._get_addresses()

    def _destroyed(self):
        if self.old_state != 'absent':
            if self.old_state == 'frozen':
                self._unfreeze_instance()
            if self.old_state != 'stopped':
                self._stop_instance()
            self._delete_instance()

    def _frozen(self):
        if self.old_state == 'absent':
            self._create_instance()
            self._start_instance()
            self._freeze_instance()
        else:
            if self.old_state == 'stopped':
                self._start_instance()
            if self._needs_to_apply_instance_configs():
                self._apply_instance_configs()
            self._freeze_instance()

    def _needs_to_change_instance_config(self, key):
        if key not in self.config:
            return False

        if key == 'config':
            # self.old_sections is already filtered for volatile keys if necessary
            old_configs = dict(self.old_sections.get(key, None) or {})
            for k, v in self.config['config'].items():
                if k not in old_configs:
                    return True
                if old_configs[k] != v:
                    return True
            return False
        else:
            old_configs = self.old_sections.get(key, {})
            return self.config[key] != old_configs

    def _needs_to_apply_instance_configs(self):
        for param in set(CONFIG_PARAMS) - set(CONFIG_CREATION_PARAMS):
            if self._needs_to_change_instance_config(param):
                return True
        return False

    def _apply_instance_configs(self):
        old_metadata = copy.deepcopy(self.old_instance).get('metadata', None) or {}
        payload = {}
        for param in set(CONFIG_PARAMS) - set(CONFIG_CREATION_PARAMS):
            if param in old_metadata:
                payload[param] = old_metadata[param]

            if self._needs_to_change_instance_config(param):
                if param == 'config':
                    payload['config'] = payload.get('config', None) or {}
                    for k, v in self.config['config'].items():
                        payload['config'][k] = v
                else:
                    payload[param] = self.config[param]
        self.diff['after']['instance'] = payload
        url = '{0}/{1}'.format(self.api_endpoint, self.name)

        if not self.module.check_mode:
            self.client.query_raw('PUT', url, payload=payload)
        self.actions.append('apply_instance_configs')

    def run(self):
        """Run the main method."""

        try:

            self.ignore_volatile_options = self.module.params.get('ignore_volatile_options')
            self.old_instance = self._get_instance_json()
            self.old_sections = dict(
                (section, content) if not isinstance(content, dict)
                else (section, dict((k, v) for k, v in content.items()
                                    if not (self.ignore_volatile_options and k.startswith('volatile.'))))
                for section, content in (self.old_instance or {}).items()
                if section in set(CONFIG_PARAMS) - set(CONFIG_CREATION_PARAMS)
            )

            self.diff['before']['instance'] = self.old_sections
            # preliminary, will be overwritten in _apply_instance_configs() if called
            self.diff['after']['instance'] = self.config

            self.old_state = self._instance_json_to_module_state(self.old_instance)
            self.diff['before']['state'] = self.old_state
            self.diff['after']['state'] = self.state

            action = getattr(self, INCUS_ANSIBLE_STATES[self.state])
            action()

            state_changed = len(self.actions) > 0
            result_json = {
                'log_verbosity': self.module._verbosity,
                'changed': state_changed,
                'old_state': self.old_state,
                'actions': self.actions,
                'diff': self.diff,
                'instance': self.diff['after']['instance'],
            }
            if self.client.debug:
                result_json['logs'] = self.client.logs
            if self.addresses is not None:
                result_json['addresses'] = self.addresses
            self.module.exit_json(**result_json)
        except IncusClientException as e:
            state_changed = len(self.actions) > 0
            fail_params = {
                'msg': e.msg,
                'changed': state_changed,
                'actions': self.actions,
                'diff': self.diff,
            }
            if self.client.debug:
                fail_params['logs'] = e.kwargs['logs']
            self.module.fail_json(**fail_params)


def main():
    """Ansible Main module."""

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(
                type='str',
                required=True,
            ),
            remote=dict(
                type='str',
                default='local',
            ),
            description=dict(
                type='str',
            ),
            project=dict(
                type='str',
                default='default',
            ),
            architecture=dict(
                type='str',
            ),
            config=dict(
                type='dict',
            ),
            ignore_volatile_options=dict(
                type='bool',
                default=False,
            ),
            devices=dict(
                type='dict',
            ),
            ephemeral=dict(
                type='bool',
            ),
            profiles=dict(
                type='list',
                elements='str',
            ),
            source=dict(
                type='dict',
            ),
            state=dict(
                choices=list(INCUS_ANSIBLE_STATES.keys()),
                default='started',
            ),
            target=dict(
                type='str',
            ),
            timeout=dict(
                type='int',
                default=30
            ),
            type=dict(
                type='str',
                default='container',
                choices=['container', 'virtual-machine'],
            ),
            wait_for_container=dict(
                type='bool',
                default=False,
            ),
            wait_for_ipv4_addresses=dict(
                type='bool',
                default=False,
            ),
            force_stop=dict(
                type='bool',
                default=False,
            ),
        ),
        supports_check_mode=True,
    )

    incus_manage = IncusInstanceManagement(module=module)
    incus_manage.run()


if __name__ == '__main__':
    main()
