# Sample responses

This document lists sample responses using `incus query` for different tasks and
is intended to help out during development.

## POST instance response

Creating a container instance called `testinstance`.

```json
{
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "operation": "",
        "error_code": 0,
        "error": "",
        "metadata": {
                "id": "a252b7bd-7178-42ca-8d94-1680254eec7b",
                "class": "task",
                "description": "Creating instance",
                "created_at": "2024-11-28T23:11:49.303545747+01:00",
                "updated_at": "2024-11-28T23:11:50.724932671+01:00",
                "status": "Success",
                "status_code": 200,
                "resources": {
                        "instances": [
                                "/1.0/instances/testinstance"
                        ]
                },
                "metadata": {
                        "create_instance_from_image_unpack_progress": "Unpacking image: 100% (3.97GB/s)",
                        "progress": {
                                "percent": "100",
                                "speed": "3972972972",
                                "stage": "create_instance_from_image_unpack"
                        }
                },
                "may_cancel": false,
                "err": "",
                "location": "none"
        }
}
```

## Get absent instance

```json
{
        "type": "error", 
        "status":"", 
        "status_code": 0, 
        "operation":"", 
        "error_code":404, 
        "error":"Not Found", 
        "metadata":null
}
```

## GET state

Using the path `/1.0/instances/testinstance/state?project=default`

```json
{
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "operation": "",
        "error_code": 0,
        "error": "",
        "metadata": {
                "status": "Stopped",
                "status_code": 102,
                "disk": {},
                "memory": {
                        "usage": 0,
                        "usage_peak": 0,
                        "total": 0,
                        "swap_usage": 0,
                        "swap_usage_peak": 0
                },
                "network": null,
                "pid": 0,
                "processes": 0,
                "cpu": {
                        "usage": 0
                },
                "started_at": "0001-01-01T00:00:00Z",
                "os_info": null
        }
}
```

## Get existing container

```json
{
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "operation": "",
        "error_code": 0,
        "error": "",
        "metadata": {
                "architecture": "aarch64",
                "config": {
                        "image.architecture": "arm64",
                        "image.description": "Debian bookworm arm64 (20241128_05:24)",
                        "image.os": "Debian",
                        "image.release": "bookworm",
                        "image.serial": "20241128_05:24",
                        "image.type": "squashfs",
                        "image.variant": "cloud",
                        "volatile.apply_template": "create",
                        "volatile.base_image": "5bfec5b4d6362bbf8755f637119ac3de7c15ca267573e47c9873388a5655e196",
                        "volatile.cloud-init.instance-id": "4f144556-ea4c-4154-8a57-91ff4346e5e1",
                        "volatile.eth0.hwaddr": "00:16:3e:9a:00:37",
                        "volatile.idmap.base": "0",
                        "volatile.idmap.next": "[{\"Isuid\":true,\"Isgid\":false,\"Hostid\":1000000,\"Nsid\":0,\"Maprange\":1000000000},{\"Isuid\":false,\"Isgid\":true,\"Hostid\":1000000,\"Nsid\":0,\"Maprange\":1000000000}]",
                        "volatile.last_state.idmap": "[]",
                        "volatile.uuid": "321b7285-2c66-4b62-924b-0c47d61ea7a0",
                        "volatile.uuid.generation": "321b7285-2c66-4b62-924b-0c47d61ea7a0"
                },
                "devices": {},
                "ephemeral": false,
                "profiles": [
                        "default"
                ],
                "stateful": false,
                "description": "",
                "created_at": "2024-11-28T22:11:50.701255415Z",
                "expanded_config": {
                        "image.architecture": "arm64",
                        "image.description": "Debian bookworm arm64 (20241128_05:24)",
                        "image.os": "Debian",
                        "image.release": "bookworm",
                        "image.serial": "20241128_05:24",
                        "image.type": "squashfs",
                        "image.variant": "cloud",
                        "volatile.apply_template": "create",
                        "volatile.base_image": "5bfec5b4d6362bbf8755f637119ac3de7c15ca267573e47c9873388a5655e196",
                        "volatile.cloud-init.instance-id": "4f144556-ea4c-4154-8a57-91ff4346e5e1",
                        "volatile.eth0.hwaddr": "00:16:3e:9a:00:37",
                        "volatile.idmap.base": "0",
                        "volatile.idmap.next": "[{\"Isuid\":true,\"Isgid\":false,\"Hostid\":1000000,\"Nsid\":0,\"Maprange\":1000000000},{\"Isuid\":false,\"Isgid\":true,\"Hostid\":1000000,\"Nsid\":0,\"Maprange\":1000000000}]",
                        "volatile.last_state.idmap": "[]",
                        "volatile.uuid": "321b7285-2c66-4b62-924b-0c47d61ea7a0",
                        "volatile.uuid.generation": "321b7285-2c66-4b62-924b-0c47d61ea7a0"
                },
                "expanded_devices": {
                        "eth0": {
                                "name": "eth0",
                                "network": "incusbr0",
                                "type": "nic"
                        },
                        "root": {
                                "path": "/",
                                "pool": "default",
                                "type": "disk"
                        }
                },
                "name": "testinstance",
                "status": "Stopped",
                "status_code": 102,
                "last_used_at": "1970-01-01T00:00:00Z",
                "location": "none",
                "type": "container",
                "project": "default"
        }
}
```
