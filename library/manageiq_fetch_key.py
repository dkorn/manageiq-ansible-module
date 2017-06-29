#!/usr/bin/python

DOCUMENTATION = ''' 
---
module: manageiq_fetch_key
description: The manageiq_fetch_key module supports pulling v2 key from a source ManageIQ appliance
short_description: Pull ManageIQ v2 key
requirements: [ ]
author: Ian Tewksbury (@itewk)
options:
  source:
    description:
      - Source ManageIQ appliance to pull the ManageIQ v2 key from
    required: true
  ssh_user:
    description:
      - SSH user to use to pull the v2 key with
    required: true
  ssh_password:
    description:
      - SSH user password to use to pull the v2 key with
    required: true
  force:
    description:
      - Ture to always pull v2 key no matter what. False to only pull the key if the destiation appliance does not already have v2 key
    required: false
    choices: ['True', 'False']
    default: 'False'
'''

EXAMPLES = ''' 
# Pull v2 key
- name: Fetch Key 
  manageiq_fetch_key:
    source: cfme-db.example.com
    ssh_user: root
    ssh_password: smartvm
    force: false
'''

def main():
    CLI    = 'appliance_console_cli'
    V2_KEY = '/var/www/miq/vmdb/certs/v2_key'

    module = AnsibleModule(
        argument_spec = dict(
            source = dict(
                required = True,
                type     = 'str',
            ),
            ssh_user = dict(
                required = True,
                type     = 'str',
            ),
            ssh_password = dict(
                required = True,
                type     = 'str',
            ),
            force = dict(
                required = False,
                type     = 'bool',
                default = False
            ),

        )
    )
    
    # ask the question and get the answer
    source       = module.params['source']
    ssh_user     = module.params['ssh_user']
    ssh_password = module.params['ssh_password']
    force        = module.params['force']

    if force:
        changed = True
        output = subprocess.check_output([CLI, '--force-key', source, '--sshlogin', ssh_user, '--sshpassword', ssh_password])
    elif not os.path.isfile(V2_KEY):
        changed = True
        output = subprocess.check_output([CLI, '--fetch-key', source, '--sshlogin', ssh_user, '--sshpassword', ssh_password])
    else:
        changed = False
      
    if changed:
        module.exit_json(
            changed = True,
            msg = 'v2_key fetched',
            output  = output
        )
    else:
        module.exit_json(
            changed = False,
            msg = 'v2_key already exists'
        )

import subprocess
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
if __name__ == '__main__':
    main()
