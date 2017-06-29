#!/usr/bin/python

DOCUMENTATION = ''' 
---
module: manageiq_join_region
description: The manageiq_join_region module supports joining a ManageIQ appliance to an existing ManageIQ region
short_description: Join ManageIQ appliance to region
requirements: [ ]
author: Ian Tewksbury (@itewk)
options:
  hostname:
    description:
      - Hostname of ManageIQ DB appliance of the region to join
    required: true
  db_password:
    description:
      - Password to the DB of the region to join
    required: true
  fetch_key:
    description:
      - True to fetch the v2 key from the given hostname. Else assume the v2 key has already been fetched.
    required: false
    choices: ['True', 'False']
    default: 'False'
  ssh_user:
    description:
      - SSH user to use to pull the v2 key with
      - Only required if fetch_key is True
    required: false
    default: 'root'
  ssh_password:
    description:
      - SSH user password to use to pull the v2 key with
      - Only required if fetch_key is True
    required: false
    default: 'smartvm'
  force:
    description:
      - True to always join the region. False to only join region if not already joined to region of the gievn host
      - Ture to always pull v2 key no matter what if fetch_key is True. False to only pull the key if the destiation appliance does not already have v2 key
    required: false
    choices: ['True', 'False']
    default: 'False'
'''

EXAMPLES = ''' 
# Join region and pull key
- name: Join Region
  manageiq_join_region:
    hostname: db.example.com
    db_password: smartvm
    fetch_key: true
    ssh_user: root
    ssh_password: smartvm

# Pull key then join region
- name: Fetch Key 
  manageiq_fetch_key:
    source: cfme-db.example.com
    ssh_user: root
    ssh_password: smartvm
    force: false

- name: Join Region
  manageiq_join_region:
    hostname: cfme-db.example.com
    db_password: smartvm
    fetch_key: true
    ssh_user: root
    ssh_password: smartvm
'''

def main():
    CLI       = 'appliance_console_cli'
    REGION    = '/var/www/miq/vmdb/REGION'
    DB_CONFIG = '/var/www/miq/vmdb/config/database.yml'
    

    module = AnsibleModule(
        argument_spec = dict(
            hostname = dict(
                required = True,
                type     = 'str',
            ),
            db_password = dict(
                required = True,
                type     = 'str',
            ),
            fetch_key = dict(
                required = False,
                type     = 'bool',
                default  = True
            ),
            ssh_user = dict(
                required = False,
                type     = 'str',
                default  = 'root'
            ),
            ssh_password = dict(
                required = False,
                type     = 'str',
                default  = 'smartvm'
            ),
            force = dict(
                required = False,
                type     = 'bool',
                default  = False
            ),
        )
    )
    
    # ask the question and get the answer
    hostname     = module.params['hostname']
    db_password  = module.params['db_password']
    fetch_key    = module.params['fetch_key']
    ssh_user     = module.params['ssh_user']
    ssh_password = module.params['ssh_password']
    force        = module.params['force']

    # add fetch key arguments if needed
    fetch_key_args = []
    if fetch_key:
        if force:
          fetch_key_args.append('--force-key')
        else:
          fetch_key_args.append('--fetch-key')
        fetch_key_args.extend([hostname, '--sshlogin', ssh_user, '--sshpassword', ssh_password])

    if force or not os.path.isfile(REGION) or hostname not in open(DB_CONFIG).read():
        changed = True
        command = [CLI]
        command.extend(fetch_key_args)
        command.extend(['--hostname', hostname, '--password', db_password])

        try:
            output = subprocess.check_output(command)
            module.exit_json(
                changed = True,
                msg = 'Joined region',
                output  = output
            )
        except subprocess.CalledProcessError as err:
            module.fail_json(
                msg = 'Failed to join region. Error Output: %s' % err.output
            )
    else:
        module.exit_json(
            changed = False,
            msg = 'Already joined to region.'
        )

import subprocess
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
if __name__ == '__main__':
    main()
