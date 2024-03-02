# -*- coding: utf-8 -*-

# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from unittest import mock
# from ansible_collections.community.general.tests.unit.compat.mock import patch
from ansible_collections.kmpm.incus.plugins.module_utils.incuscli import IncusClient


@mock.patch("ansible_collections.kmpm.incus.plugins.module_utils.incuscli.get_bin_path", side_effect=ValueError('boom'))
def test_valid_invalid_bin(_get_bin_path):
    # print(dir(_get_bin_path))
    with pytest.raises(ValueError):
        _get_bin_path.return_value = ''
        client = IncusClient()
        # _get_bin_path.assert_called_once()


@mock.patch("ansible_collections.kmpm.incus.plugins.module_utils.incuscli.get_bin_path", autospec=True)
def test_instanciation(_get_bin_path):
    _get_bin_path.return_value = '/usr/bin/incus'
    client = IncusClient()
    _get_bin_path.assert_called_once()
    assert client is not None
    # result = client.do('GET', '/')
    # print(result)
    # assert 'status' in result
    # assert 'status_code' in result
    # assert result['status_code'] == 200
    # assert result['metadata'] == ['/1.0']
