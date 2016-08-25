#!/usr/bin/python

from ansible.module_utils.basic import *
from miqclient.api import API as MiqApi


PROVIDER_TYPE = 'ManageIQ::Providers::OpenshiftEnterprise::ContainerManager'
PROVIDER_SUFFIX = '/providers'

DOCUMENTATION = '''
---
module: manageiq
short_description: Execute various operations in ManageIQ
requirements: [ ManageIQ/manageiq-api-client-python ]
author: Daniel Korn (dkorn)
options:
  url:
    description:
      - 'the manageiq environment url'
    required: true
    default: []
  username:
    description:
      - 'manageiq username'
    required: true
    default: []
  password:
    description:
      - 'manageiq password'
    required: true
    default: []
  name:
    description:
      - 'the added provider name in manageiq'
    required: true
    default: []
  hostname:
    description:
      - 'the added provider hostname'
    required: true
    default: []
  port:
    description:
      - 'the port used by the added provider'
    required: true
    default: []
  token:
    description:
      - 'the added provider token'
    required: true
    default: []
'''

EXAMPLES = '''
# Add Openshift Containers Provider to ManageIQ
  manageiq:
    name: 'Molecule'
    url: 'http://localhost:3000'
    username: 'admin'
    password: '******'
    hostname: 'oshift01.redhat.com'
    port: '8443'
    token: '******'
'''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            url=dict(required=True),
            username=dict(required=True),
            password=dict(required=True),
            port=dict(required=True),
            hostname=dict(required=True),
            token=dict(required=True)
        )
    )

    params = module.params
    url = params['url'] + '/api'
    providers_url = url + '/providers'
    username = params['username']
    password = params['password']
    provider_name = params['name']
    port = params['port']
    hostname = params['hostname']
    token = params['token']

    endpoints = [{'endpoint': {'role': 'default', 'hostname': hostname,
                               'port': port},
                  'authentication': {'role': 'Bearer',
                                     'auth_key': token}}]

    client = MiqApi(url, (username, password))
    providers = client.collections.providers
    # check if provider with the same name already exists
    provider_id = None
    for provider in providers:
        if provider.name == provider_name:
            provider_id = provider.id
    if provider_id:
        # provider exists, updates provider with new parameters
        try:
            result = client.post(providers_url + '/' + str(provider_id),
                                 action='edit',
                                 connection_configurations=endpoints)
            msg = "Successfuly updated %s provider" % provider_name
            changed = True
        except Exception as e:
            msg = "Failed to add provider. Error: %s" % e
            module.fail_json(msg=msg)
    # provider doesn't exists, adding it to manageiq
    else:
        try:
            result = client.post(providers_url, type=PROVIDER_TYPE,
                                 name=provider_name,
                                 connection_configurations=endpoints)
            provider_id = result['results'][0]['id']
            msg = "Successfuly added %s provider" % provider_name
            changed = True
        except Exception as e:
            msg = "Failed to add provider. Error: %s" % e
            module.fail_json(msg=msg)

    res_args = dict(
        provider_id=provider_id, changed=changed, msg=msg
    )
    module.exit_json(**res_args)


main()
