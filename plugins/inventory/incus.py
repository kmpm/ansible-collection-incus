# -*- coding: utf-8 -*-
# Copyright (c) 2024, Peter Magnusson <me@kmpm.se>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
    name: incus
    short_description: Incus inventory source
    description:
      - Reads inventory from Incus using the Incus Command Line Interface (CLI).
      - Uses a file that ends with C(incus.yml) or C(incus.yaml).
    requirements:
        - ipaddress
        - incus CLI installed
    options:
      plugin:
        description: Name of the plugin
        required: true
        choices: ['kmpm.incus.incus']
      project:
        description: The name of the Incus project to use (per C(incus project list)).
        default: default
      type_filter:
        description:
          - Filter the instances by type V(virtual-machine), V(container) or V(all).
        type: str
        default: container
        choices: [ 'vm', 'container', 'all' ]
      state_filter:
        description: Filter the instances by state V(running), V(stopped) or V(all).
        type: str
        default: running
        choices: [ 'running', 'stopped', 'all' ]
      prefered_instance_network_interface:
        description: The name of the network interface to use for the ansible_host variable.
        type: str
        default: eth
      prefered_instance_network_family:
        description:
          - The network family to use for the ansible_host variable.
          - Specify V(inet) for IPv4 and V(inet6) for IPv6.
        type: str
        default: inet
        choices: [ 'inet', 'inet6' ]
      groupby:
        description:
        - Create groups by the following keywords C(location), C(network_range), C(os), C(pattern), C(profile), C(release), C(type), C(vlanid).
        - See example for syntax.
        type: dict
'''

import traceback
import re
from typing import List, Dict, Any
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.module_utils.common.yaml import yaml_load
from ansible.module_utils.six import raise_from
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable, Constructable
from ansible_collections.kmpm.incus.plugins.module_utils.incuscli import IncusClient

try:
    from yaml.scanner import ScannerError
except ImportError:
    class ScannerError(Exception):
        pass

try:
    import ipaddress
    HAS_IPADDRESS = True
except ImportError as exc:
    IPADDRESS_IMPORT_ERROR = traceback.format_exc()
    HAS_IPADDRESS = False
else:
    IPADDRESS_IMPORT_ERROR = None


class InventoryModule(BaseInventoryPlugin, Cacheable, Constructable):
    NAME = 'kmpm.incus.incus'
    DEBUG = 4

    def __init__(self):
        super(InventoryModule, self).__init__()
        self.project = None
        self.plugin = None

    def load_yaml_data(self, filepath):
        try:
            with open(filepath, 'r') as f:
                return yaml_load(f)
        except (IOError, ScannerError) as err:
            raise AnsibleParserError('Could not load the test data from {0}: {1}'.format(to_native(filepath), to_native(err)))

    def verify_file(self, path):
        '''Return true/false if this is possibly the correct source handler for the file'''
        if super(InventoryModule, self).verify_file(path):
            return path.endswith(('incus.yml', 'incus.yaml'))
        self.display.vvv(f"{path} is not a valid file or does not end with incus.yml or incus.yaml")
        return False

    def parse(self, inventory: Any, loader: Any, path: Any, cache: bool = True) -> Any:
        if IPADDRESS_IMPORT_ERROR:
            raise_from(
                AnsibleError('another_library must be installed to use this plugin'),
                IPADDRESS_IMPORT_ERROR)

        super(InventoryModule, self).parse(inventory, loader, path, cache)
        self._read_config_data(path)
        try:
            self.plugin = self.get_option('plugin')
            self.project = self.get_option('project')
            self.type_filter = self.get_option('type_filter')
            self.state_filter = self.get_option('state_filter')
            self.prefered_instance_network_interface = self.get_option('prefered_instance_network_interface')
            self.prefered_instance_network_family = self.get_option('prefered_instance_network_family')
            self.groupby = self.get_option('groupby')
            self.debug = self.DEBUG
            self.data = {}
        except KeyError as kerr:
            raise AnsibleParserError(f"Missing required configuration parameter: {kerr}")

        self._populate()

    def _populate(self):
        cli = IncusClient(remote='local', project=self.project, debug=True)
        if len(self.data) == 0:
            self.data = cli.list()
            self.display.vvv(f"Inventory data: {self.data}")
        # TODO: filtering
        self.build_inventory()

    def _cleandata(self):
        '''Clean up the inventory data and remove anything not matching filter'''
        def keep_instance(instance):
            if self.project and instance['project'] != self.project:
                return False
            if self.type_filter != 'all' and instance['type'] != self.type_filter:
                return False
            if self.state_filter != 'all' and instance['state']['status'].lower() != self.state_filter:
                return False
            return True

        self.data = [instance for instance in self.data if keep_instance(instance)]

    def _get_instance(self, instance_name: str) -> Dict[str, Any]:
        '''Get instance by name'''
        for instance in self.data:
            if instance['name'] == instance_name:
                return instance
        return KeyError(f"Instance {instance_name} not found")

    def _get_network_addresses(self, instance_name: str) -> List[Dict[str, Any]]:
        """Get the interfaces for a given instance"""
        instance = self._get_instance(instance_name)

        networks = instance['state']['network']
        rows = []
        for iface in networks.keys():
            base = {
                'iface': iface,
                'type': networks[iface]['type'],
                'state': networks[iface]['state'],
            }
            for adr in networks[iface]['addresses']:
                entry = {**base, **adr}
                rows.append(entry)
        return rows

    def _get_interface(self, instance: Any):
        network = instance['state']['network']
        self.display.vvv(f"Network: {network}")
        for name in network.keys():
            if name.startswith(self.prefered_instance_network_interface):
                for adr in network[name]['addresses']:
                    if adr['family'] == self.prefered_instance_network_family:
                        adr['name'] = name
                        return adr
        return None

    def _get_config_value(self, instance, key):
        try:
            return instance['config'][key]
        except KeyError:
            return None

    def _build_group_from_var(self, group_name, var_name):
        if group_name not in self.inventory.groups:
            self.inventory.add_group(group_name)

        for instance_name in self.inventory.hosts:
            if var_name in self.inventory.get_host(instance_name).get_vars():
                self.inventory.add_child(group_name, instance_name)

    def _build_group_from_var_equals(self, group_name: str, var_name: str, want: Any):
        if group_name not in self.inventory.groups:
            self.inventory.add_group(group_name)
        want = want.lower()
        for instance_name in self.inventory.hosts:
            if var_name in self.inventory.get_host(instance_name).get_vars():
                got = self.inventory.get_host(instance_name).get_vars().get(var_name)
                _t = type(got)
                match(_t):
                    case s if issubclass(_t, str):
                        if want in got.lower():
                            self.inventory.add_child(group_name, instance_name)
                    case l if issubclass(_t, list):
                        if want in got:
                            self.inventory.add_child(group_name, instance_name)
                    case _:
                        # could possibly fail here if an exotic comparison is needed
                        if want == got:
                            self.inventory.add_child(group_name, instance_name)

    def _build_group_from_pattern(self, group_name, pattern):
        if group_name not in self.inventory.groups:
            self.inventory.add_group(group_name)

        regexp_pattern = re.compile(pattern)

        for instance_name in self.inventory.hosts:
            if regexp_pattern.search(instance_name):
                self.inventory.add_child(group_name, instance_name)

    def _build_group_from_network_range(self, group_name, network_range):
        if group_name not in self.inventory.groups:
            self.inventory.add_group(group_name)

        try:
            network = ipaddress.ip_network(network_range)
        except ValueError as e:
            raise AnsibleParserError(f"Invalid network range: {e}")

        for instance_name in self.inventory.hosts:
            rows = self._get_network_addresses(instance_name)
            for family in rows:
                try:
                    address = ipaddress.ip_address(to_text(family['address']))
                    if address.version == network.version and address in network:
                        self.inventory.add_child(group_name, instance_name)
                except ValueError:
                    pass

    def build_inventory_groups(self):
        groupmap = {
            'location': 'ansible_incus_location',
            'os': 'ansible_incus_os',
            'profile': 'ansible_incus_profiles',
            'release': 'ansible_incus_release',
            'type': 'ansible_incus_type',

            'pattern': self._build_group_from_pattern,
            'network_range': self._build_group_from_network_range,
            # FIXME: 'vlanid': 'ansible_incus_vlan_ids',
        }

        if self.groupby:
            for group_name in self.groupby:
                if not group_name.isalnum():
                    raise AnsibleParserError('Invalid character(s) in groupname: {0}'.format(to_native(group_name)))
                group_type = self.groupby[group_name].get('type')
                if group_type not in groupmap:
                    raise AnsibleParserError('Invalid group type: {0}'.format(to_native(group_type)))
                group_var = groupmap[group_type]
                if callable(group_var):
                    group_var(group_name, self.groupby[group_name].get('attribute'))
                    continue
                group_value = self.groupby[group_name].get('attribute')
                # TODO: possibly leave attribute empty and group without equals
                self._build_group_from_var_equals(group_name, group_var, group_value)

    def build_inventory_hosts(self):
        for instance in self.data:
            instance_name = instance['name']
            self.inventory.add_host(instance_name)
            instance_type = instance['type']
            instance_status = instance['status'].lower()
            self.inventory.set_variable(instance_name, 'ansible_incus_type', instance_type)
            self.inventory.set_variable(instance_name, 'ansible_incus_status', instance_status)
            self.inventory.set_variable(instance_name, 'ansible_incus_profiles', instance['profiles'])
            self.inventory.set_variable(instance_name, 'ansible_incus_location', instance['location'])
            self.inventory.set_variable(instance_name, 'ansible_incus_architecture', instance['architecture'])

            self.inventory.set_variable(instance_name, 'ansible_incus_os', self._get_config_value(instance, 'image.os'))
            self.inventory.set_variable(instance_name, 'ansible_incus_release', self._get_config_value(instance, 'image.release'))

            iface = self._get_interface(instance)
            if iface:
                self.inventory.set_variable(instance_name, 'ansible_host', iface['address'])
                # FIXME: vlanid
                self.inventory.set_variable(instance_name, 'ansible_incus_vlan_ids', None)
            if instance['type'] == 'container':
                self.inventory.set_variable(instance_name, 'ansible_connection', 'community.general.incus')
            elif iface:
                self.inventory.set_variable(instance_name, 'ansible_connection', 'ssh')

    def build_inventory(self):
        self.build_inventory_hosts()
        self.build_inventory_groups()
