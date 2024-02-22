# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.kmpm.general.plugins.module_utils import incus

def test_valid_api_endpoints():
    client =  incus.IncusClient(url='unix:/var/lib/incus/unix.socket')
    assert client is not None
    result = client.do('GET', '/')
    print(result)
    assert 'status' in result
    assert 'status_code' in result
    assert result['status_code'] == 200
    assert result['metadata'] == ['/1.0']

