#!/usr/bin/python

from ansible.module_utils.basic import *
from miqclient.api import API as MiqApi


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


class ManageIQ(object):
    """ ManageIQ object to execute various operations in manageiq

    url      - manageiq environment url
    user     - the username in manageiq
    password - the user password in manageiq
    """
    openshift_provider_type = 'ManageIQ::Providers::OpenshiftEnterprise::ContainerManager'

    def __init__(self, module, url, user, password):
        self.module        = module
        self.api_url       = url + '/api'
        self.user          = user
        self.password      = password
        self.client        = MiqApi(self.api_url, (self.user, self.password))
        self.changed       = False
        self.providers_url = self.api_url + '/providers'

    def update_required(self, provider_id, hostname, port):
        """ Checks whether an update is required for the provider

        Returns:
            False if the hostname and port passed equals the provider's,
            True otherwise
        """
        try:
            result = self.client.get(self.providers_url + '/%d/?attributes=authentications,endpoints' % provider_id)
        except Exception as e:
            self.module.fail_json(msg="Failed to get provider data. Error: %s" % e)
        endpoint = result['endpoints'][0]
        return False if (endpoint['hostname'] == hostname and endpoint['port'] == int(port)) else True

    def update_provider(self, provider_id, provider_name, endpoints):
        """ Updates the existing provider with new parameters
        """
        try:
            self.client.post(self.providers_url + '/%d' % provider_id,
                             action='edit',
                             connection_configurations=endpoints)
            self.changed = True
        except Exception as e:
            self.module.fail_json(msg="Failed to update provider. Error: %s" % e)

    def add_new_provider(self, provider_name, endpoints):
        """ Adds a provider to manageiq

        Returns:
            the added provider id
        """
        try:
            result = self.client.post(self.providers_url, type=ManageIQ.openshift_provider_type,
                                      name=provider_name,
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

    def add_or_update_provider(self, provider_name, hostname, port, token):
        """ Adds an OpenShift containers provider to manageiq or update it's
        attributes in case a provider with the same name already exists

        Returns:
            the added or updated provider id, whether or not a change took place
            and a short message describing the operation executed
        """
        endpoints = [{'endpoint': {'role': 'default', 'hostname': hostname,
                                   'port': port},
                     'authentication': {'role': 'bearer',
                                        'auth_key': token}}]
        message = ""

        # check if provider with the same name already exists
        provider_id = self.find_provider_by_name(provider_name)
        if provider_id:  # provider exists
            if self.update_required(provider_id, hostname, port):
                self.update_provider(provider_id, provider_name, endpoints)
                message = "Successfuly updated %s provider" % provider_name
            else:
                message = "Provider %s already exists" % provider_name
        else:  # provider doesn't exists, adding it to manageiq
            provider_id = self.add_new_provider(provider_name, endpoints)
            message = "Successfuly added %s provider" % provider_name

        res_args = dict(
            provider_id=provider_id, changed=self.changed, msg=message
        )
        return res_args


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            url=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            port=dict(required=True),
            hostname=dict(required=True),
            token=dict(required=True, no_log=True)
        )
    )

    url           = module.params['url']
    username      = module.params['username']
    password      = module.params['password']
    provider_name = module.params['name']
    hostname      = module.params['hostname']
    port          = module.params['port']
    token         = module.params['token']

    manageiq = ManageIQ(module, url, username, password)

    res_args = manageiq.add_or_update_provider(provider_name, hostname, port, token)
    module.exit_json(**res_args)


main()
