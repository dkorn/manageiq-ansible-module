#!/usr/bin/python

import os
from ansible.module_utils.basic import *
from miqclient.api import API as MiqApi


DOCUMENTATION = '''
---
module: manageiq
short_description: Execute various operations in ManageIQ
requirements: [ ManageIQ/manageiq-api-client-python ]
author: Daniel Korn (@dkorn)
options:
  url:
    description:
      - the manageiq environment url
    default: MIQ_URL env var if set. otherwise, it is required to pass it
  username:
    description:
      - manageiq username
    default: MIQ_USERNAME env var if set. otherwise, it is required to pass it
  password:
    description:
      - manageiq password
    default: MIQ_PASSWORD env var if set. otherwise, it is required to pass it
  name:
    description:
      - the added provider name in manageiq
    required: true
    default: null
  type:
    description:
      - the openshift provider type
    required: true
    choices: ['openshift-origin', 'openshift-enterprise']
  hostname:
    description:
      - the added provider hostname
    required: true
    default: null
  port:
    description:
      - the port used by the added provider
    required: true
    default: null
  token:
    description:
      - the added provider token
    required: true
    default: null
  metrics:
    description:
      - whether metrics should be enabled in the provider
    required: false
    default: False
    choices: ['True', 'False']
  hawkular_hostname:
    description:
      - the hostname used for hawkular metrics
    required: false
    default: null
  hawkular_port:
    description:
      - the port used for hawkular metrics
    required: false
    default: null
'''

EXAMPLES = '''
# Add Openshift Containers Provider to ManageIQ
  manageiq:
    name: 'Molecule'
    type: 'openshift-enterprise'
    url: 'http://localhost:3000'
    username: 'admin'
    password: '******'
    hostname: 'oshift01.redhat.com'
    port: '8443'
    token: '******'
    metrics: True
    hawkular_hostname: 'hawkular01.redhat.com'
    hawkular_port: '443'
'''


class ManageIQ(object):
    """ ManageIQ object to execute various operations in manageiq

    url      - manageiq environment url
    user     - the username in manageiq
    password - the user password in manageiq
    """
    openshift_provider_types = {'openshift-origin': 'ManageIQ::Providers::Openshift::ContainerManager',
                                'openshift-enterprise': 'ManageIQ::Providers::OpenshiftEnterprise::ContainerManager'}

    def __init__(self, module, url, user, password):
        self.module        = module
        self.api_url       = url + '/api'
        self.user          = user
        self.password      = password
        self.client        = MiqApi(self.api_url, (self.user, self.password))
        self.changed       = False
        self.providers_url = self.api_url + '/providers'

    def update_required(self, provider_id, endpoints):
        """ Checks whether an update is required for the provider

        Returns:
            False if the hostname and port passed equals the provider's,
            True otherwise
        """
        try:
            result = self.client.get('{providers_url}/{id}/?attributes=authentications,endpoints'.format(providers_url=self.providers_url, id=provider_id))
        except Exception as e:
            self.module.fail_json(msg="Failed to get provider data. Error: %s" % e)

        def host_port(endpoint):
            return (endpoint['hostname'], int(endpoint['port']))

        desired_by_role = {e['endpoint']['role']: host_port(e['endpoint']) for e in endpoints}
        result_by_role = {e['role']: host_port(e) for e in result['endpoints']}
        return desired_by_role != result_by_role

    def update_provider(self, provider_id, provider_name, endpoints):
        """ Updates the existing provider with new parameters
        """
        try:
            self.client.post('{api_url}/providers/{id}'.format(api_url=self.api_url, id=provider_id),
                             action='edit',
                             connection_configurations=endpoints)
            self.changed = True
        except Exception as e:
            self.module.fail_json(msg="Failed to update provider. Error: %s" % e)

    def add_new_provider(self, provider_name, provider_type, endpoints):
        """ Adds a provider to manageiq

        Returns:
            the added provider id
        """
        try:
            result = self.client.post(self.providers_url, name=provider_name,
                                      type=ManageIQ.openshift_provider_types[provider_type],
                                      connection_configurations=endpoints)
            provider_id = result['results'][0]['id']
            self.changed = True
        except Exception as e:
            self.module.fail_json(msg="Failed to add provider. Error: %s" % e)
        return provider_id

    def find_provider_by_name(self, provider_name):
        """ Searches the provider name in manageiq existing providers

        Returns:
            the provider id if it exists in manageiq, None otherwise
        """
        providers = self.client.collections.providers
        return next((p.id for p in providers if p.name == provider_name), None)

    def generate_endpoint(self, role, hostname, port, authtype, token):
        """ Returns one provider endpoint hash.
        """
        return {'endpoint': {'role': role, 'hostname': hostname,
                             'port': port},
                'authentication': {'role': authtype, 'auth_key': token}}

    def add_or_update_provider(self, provider_name, provider_type, endpoints):
        """ Adds an OpenShift containers provider to manageiq or update it's
        attributes in case a provider with the same name already exists

        Returns:
            the added or updated provider id, whether or not a change took place
            and a short message describing the operation executed
        """
        message = ""
        # check if provider with the same name already exists
        provider_id = self.find_provider_by_name(provider_name)
        if provider_id:  # provider exists
            if self.update_required(provider_id, endpoints):
                self.update_provider(provider_id, provider_name, endpoints)
                message = "Successfuly updated %s provider" % provider_name
            else:
                message = "Provider %s already exists" % provider_name
        else:  # provider doesn't exists, adding it to manageiq
            provider_id = self.add_new_provider(provider_name, provider_type, endpoints)
            message = "Successfuly added %s provider" % provider_name

        res_args = dict(
            provider_id=provider_id, changed=self.changed, msg=message
        )
        return res_args


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            type=dict(required=True,
                      choices=['openshift-origin', 'openshift-enterprise']),
            url=dict(default=os.environ.get('MIQ_URL', None)),
            username=dict(default=os.environ.get('MIQ_USERNAME', None)),
            password=dict(default=os.environ.get('MIQ_PASSWORD', None)),
            port=dict(required=True),
            hostname=dict(required=True),
            token=dict(required=True, no_log=True),
            metrics=dict(required=False, type='bool', default=False),
            hawkular_hostname=dict(required=False),
            hawkular_port=dict(required=False)
        ),
        required_if=[
            ('metrics', True, ['hawkular_hostname', 'hawkular_port']),
        ],
    )

    for arg in ['url', 'username', 'password']:
        if module.params[arg] in (None, ''):
            module.fail_json(msg="missing required argument: {}".format(arg))

    url           = module.params['url']
    username      = module.params['username']
    password      = module.params['password']
    provider_name = module.params['name']
    provider_type = module.params['type']
    hostname      = module.params['hostname']
    port          = module.params['port']
    token         = module.params['token']
    h_hostname    = module.params['hawkular_hostname']
    h_port        = module.params['hawkular_port']

    manageiq = ManageIQ(module, url, username, password)

    endpoints = [manageiq.generate_endpoint('default', hostname, port, 'bearer', token)]
    if module.params['metrics']:
        endpoints += [manageiq.generate_endpoint('hawkular', h_hostname, h_port, 'hawkular', token)]

    res_args = manageiq.add_or_update_provider(provider_name, provider_type, endpoints)
    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
