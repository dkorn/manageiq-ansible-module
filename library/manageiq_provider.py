#!/usr/bin/python

import os
import time
from ansible.module_utils.basic import *
from manageiq_client.api import ManageIQClient as MiqApi


DOCUMENTATION = '''
---
module: manageiq_provider
description: The manageiq_provider module currently supports adding, updating and deleting OpenShift, Amazon EC2 and Hawkular Datawarehouse providers to ManageIQ.
short_description: add, update, delete provider in ManageIQ
requirements: [ ManageIQ/manageiq-api-client-python ]
author: Daniel Korn (@dkorn)
options:
  miq_url:
    description:
      - the manageiq environment url
    default: MIQ_URL env var if set. otherwise, it is required to pass it
  miq_username:
    description:
      - manageiq username
    default: MIQ_USERNAME env var if set. otherwise, it is required to pass it
  miq_password:
    description:
      - manageiq password
    default: MIQ_PASSWORD env var if set. otherwise, it is required to pass it
  miq_verify_ssl:
    description:
      - whether SSL certificates should be verified for HTTPS requests to ManageIQ
    required: false
    default: True
    choices: ['True', 'False']
  ca_bundle_path:
    description:
      - the path to a CA_BUNDLE file or directory with certificates
    required: false
    default: null
  name:
    description:
      - the added provider name in manageiq
    required: true
    default: null
  provider_type:
    description:
      - the provider's type
    required: true
    choices: ['openshift-origin', 'openshift-enterprise', 'amazon', 'hawkular-datawarehouse']
  state:
    description:
      - the state of the provider
      - On present, it will add the provider if it does not exist or update the
        provider if the associated data is different
      - On absent, it will delete the provider if it exists
    required: false
    choices: ['present', 'absent']
    default: 'present'
  zone:
    description:
      - the provider zone name in manageiq
    required: false
    default: null
  provider_api_hostname:
    description:
      - the provider API hostname
    required: true
    default: null
  provider_api_port:
    description:
      - the port used by the provider API
    required: true
    default: null
  provider_api_auth_token:
    description:
      - the provider api auth token
    required: true
    default: null
  provider_verify_ssl:
    description:
      - whether SSL certificates should be verified for HTTPS requests between
        ManageIQ and the provider
    required: false
    default: True
    choices: ['True', 'False']
  provider_ca_path:
    description:
      - the path to the ca file
      - to remove a previously defined ca pass "" (empty string)
      - in case the parameter is passed with null or omitted the
        certificate_authority field will be left unmodified
        (unset on creation).
      - must be omitted with ManageIQ Euwe / CFME 5.7 or earlier releases
    required: false
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
  manageiq_provider:
    name: 'Molecule'
    provider_type: 'openshift-enterprise'
    state: 'present'
    miq_url: 'http://miq.example.com'
    miq_username: 'admin'
    miq_password: '******'
    zone: 'default'
    provider_api_hostname: 'oshift01.redhat.com'
    provider_api_port: '8443'
    provider_api_auth_token: '******'
    miq_verify_ssl: false
    provider_verify_ssl: false
    metrics: True
    hawkular_hostname: 'hawkular01.redhat.com'
    hawkular_port: '443'

# Remove Openshift Provider from HTTPS ManageIQ environment
  manageiq_provider:
    name: 'OS01'
    provider_type: 'openshift-enterprise'
    state: 'absent'
    miq_url: 'https://miq.example.com'
    miq_username: 'admin'
    miq_password: '******'
    miq_verify_ssl: true
    ca_bundle_path: '/path/to/certfile'
    provider_verify_ssl: true
    provider_ca_path: '/path/to/provider/certfile'
    provider_api_hostname: 'oshift01.redhat.com'
    provider_api_port: '8443'
    provider_api_auth_token: '******'

# Add Amazon EC2 Cloud provider to ManageIQ
  manageiq_provider:
    name: 'AWS01'
    provider_type: 'amazon'
    provider_region: 'us-west-2"
    access_key_id: '******'
    secret_access_key: '******'
    state: 'present'
    miq_verify_ssl: false
    miq_url: 'http://localhost:3000'
    miq_username: 'admin'
    miq_password: '******'

# name: Add Hawkular Datawarehouse Provider to ManageIQ
  manageiq_provider:
    name: 'HawkDW01'
    provider_type: 'hawkular-datawarehouse'
    state: 'present'
    provider_api_hostname: 'hawk.example.com'
    provider_api_port: '443'
    provider_api_auth_token: '******'
    miq_url: 'http://miq.example.com'
    miq_username: 'admin'
    miq_password: '******'
    miq_verify_ssl: false
'''


class ManageIQProvider(object):
    """ ManageIQ object to execute various operations in manageiq

    url            - manageiq environment url
    user           - the username in manageiq
    password       - the user password in manageiq
    miq_verify_ssl - whether SSL certificates should be verified for HTTPS requests
    ca_bundle_path - the path to a CA_BUNDLE file or directory with certificates
    """

    OPENSHIFT_DEFAULT_PORT = '8443'

    PROVIDER_TYPES = {
        'openshift-origin': 'ManageIQ::Providers::Openshift::ContainerManager',
        'openshift-enterprise': 'ManageIQ::Providers::OpenshiftEnterprise::ContainerManager',
        'amazon': 'ManageIQ::Providers::Amazon::CloudManager',
        'hawkular-datawarehouse': "ManageIQ::Providers::Hawkular::DatawarehouseManager",
    }

    WAIT_TIME = 5
    ITERATIONS = 10

    def __init__(self, module, url, user, password, miq_verify_ssl, ca_bundle_path):
        self.module        = module
        self.api_url       = url + '/api'
        self.user          = user
        self.password      = password
        self.client        = MiqApi(self.api_url, (self.user, self.password), verify_ssl=miq_verify_ssl, ca_bundle_path=ca_bundle_path)
        self.changed       = False
        self.providers_url = self.api_url + '/providers'

    def auths_validation_details(self, provider_id):
        try:
            result = self.client.get('{providers_url}/{id}/?attributes=authentications'.format(providers_url=self.providers_url, id=provider_id))
            auths = result.get('authentications', [])
            return {auth['authtype']: auth for auth in auths}
        except Exception as e:
            self.module.fail_json(msg="Failed to get provider data. Error: %s" % e)

    def verify_authenticaion_validation(self, provider_id, old_validation_details, authtypes_to_verify):
        """ Verifies that the provider's authentication validation passed.
        provider_id            - the provider's id manageiq
        old_validation_details - a tuple of (last_valid_on, last_invalid_on), representing the last time
                                 that the authentication validation occured (success or failure).
        authtypes_to_verify    - a list of autentication types that require validation

        Returns a (result, details) tuple:
            result: 'Valid' if authentication validation passed for all endpoints, 'Invalid' if failed for any endpoint,
                    'Timed out' if any validation didn't complete in the assigned time
            details: Authentication validation details, 'Validation didn't complete' in case it timed out
        """
        def validated(old, new):
            """ Returns True if the validation timestamp, valid or invalid, is different
            from the old validation timestamp, False otherwise
            """
            return ((old.get('last_valid_on'), old.get('last_invalid_on')) !=
                    (new.get('last_valid_on'), new.get('last_invalid_on')))

        for i in range(ManageIQProvider.ITERATIONS):
            new_validation_details = self.auths_validation_details(provider_id)

            validations_done = True
            all_done_valid = "Valid"  # Out of the (re)validated ones.
            details = {}
            for t in authtypes_to_verify:
                old = old_validation_details.get(t, {})
                new = new_validation_details.get(t, {})
                if not validated(old, new):
                    details[t] = "Validation didn't complete"
                    validations_done = False
                else:
                    details[t] = (new.get('status'), new.get('status_details'))
                    if new.get('status') != 'Valid':
                        all_done_valid = "Invalid"

            if validations_done:
                return all_done_valid, details
            time.sleep(ManageIQProvider.WAIT_TIME)

        return "Timed out", details

    def required_updates(self, provider_id, endpoints, zone_id, provider_region):
        """ Checks whether an update is required for the provider

        Returns:
            Empty Hash (None) - If the hostname, port, zone and region passed equals
                                the provider's current values
            Hash of Changes   - Changes that need to be made if any endpoint, zone
                                or region are different than the current values of the
                                provider. The hash will have three entries:
                                    Updated, Removed, Added
                                that will contain all the changed endpoints
                                and their values.
        """
        try:
            result = self.client.get('{providers_url}/{id}/?attributes=endpoints'.format(providers_url=self.providers_url, id=provider_id))
        except Exception as e:
            self.module.fail_json(msg="Failed to get provider data. Error: {!r}".format(e))

        def host_port(endpoint):
            return {'hostname': endpoint.get('hostname'), 'port': endpoint.get('port')}

        # TODO (dkorn/cben): add provider_verify_ssl and provider_ca_content comparison
        desired_by_role = {e['endpoint']['role']: host_port(e['endpoint']) for e in endpoints}
        result_by_role = {e['role']: host_port(e) for e in result['endpoints']}
        existing_provider_region = result.get('provider_region') or None
        if result_by_role == desired_by_role and result['zone_id'] == zone_id and existing_provider_region == provider_region:
            return {}
        updated = {role: {k: v for k, v in ep.items()
                          if k not in result_by_role[role] or v != result_by_role[role][k]}
                   for role, ep in desired_by_role.items()
                   if role in result_by_role and ep != result_by_role[role]}
        added = {role: ep for role, ep in desired_by_role.items()
                 if role not in result_by_role}
        removed = {role: ep for role, ep in result_by_role.items()
                   if role not in desired_by_role}
        if result['zone_id'] != zone_id:
            updated['zone_id'] = zone_id
        if existing_provider_region != provider_region:
            updated['provider_region'] = provider_region
        return {"Updated": updated, "Added": added, "Removed": removed}

    def refresh_provider(self, provider_id):
        """ Performs a refresh of provider's inventory
        """
        try:
            self.client.post('{api_url}/providers/{id}'.format(api_url=self.api_url, id=provider_id),
                             action='refresh')
            self.changed = True
        except Exception as e:
            self.module.fail_json(msg="Failed to refresh provider. Error: {!r}".format(e))

    def update_provider(self, provider_id, provider_name, endpoints, zone_id, provider_region):
        """ Updates the existing provider with new parameters
        """
        try:
            self.client.post('{api_url}/providers/{id}'.format(api_url=self.api_url, id=provider_id),
                             action='edit',
                             zone={'id': zone_id},
                             connection_configurations=endpoints,
                             provider_region=provider_region)
            self.changed = True
        except Exception as e:
            self.module.fail_json(msg="Failed to update provider. Error: {!r}".format(e))

    def add_new_provider(self, provider_name, provider_type, endpoints, zone_id, provider_region):
        """ Adds a provider to manageiq

        Returns:
            the added provider id
        """
        try:
            result = self.client.post(self.providers_url, name=provider_name,
                                      type=ManageIQProvider.PROVIDER_TYPES[provider_type],
                                      zone={'id': zone_id},
                                      connection_configurations=endpoints,
                                      provider_region=provider_region)
            provider_id = result['results'][0]['id']
            self.changed = True
        except Exception as e:
            self.module.fail_json(msg="Failed to add provider. Error: {!r}".format(e))
        return provider_id

    def find_zone_by_name(self, zone_name):
        """ Searches the zone name in manageiq existing zones

        Returns:
            the zone id if it exists in manageiq, None otherwise
        """
        zones = self.client.collections.zones
        return next((z.id for z in zones if z.name == zone_name), None)

    def find_provider_by_name(self, provider_name):
        """ Searches the provider name in manageiq existing providers

        Returns:
            the provider id if it exists in manageiq, None otherwise
        """
        providers = self.client.collections.providers
        return next((p.id for p in providers if p.name == provider_name), None)

    def generate_auth_key_config(self, role, authtype, hostname, port, token, provider_verify_ssl, provider_ca_path):
        """ Returns an openshift provider endpoint dictionary.
        """
        config = {'endpoint': {'role': role, 'hostname': hostname,
                               'port': int(port),
                               'verify_ssl': provider_verify_ssl},
                  'authentication': {'authtype': authtype, 'auth_key': token}}

        if provider_ca_path:
            with open(provider_ca_path, 'r') as provider_ca_file:
                provider_ca_content = provider_ca_file.read()
                config['endpoint']['certificate_authority'] = provider_ca_content
        elif provider_ca_path == "":
            config['endpoint']['certificate_authority'] = ""

        return config

    def generate_amazon_config(self, role, authtype, userid, password):
        """ Returns an amazon provider endpoint dictionary.
        """
        return {'endpoint': {'role': role},
                'authentication': {'authtype': authtype, 'userid': userid,
                                   'password': password}}

    def delete_provider(self, provider_name):
        """ Deletes the provider

        Returns:
            the delete task id if a task was generated, whether or not
            a change took place and a short message describing the operation
            executed.
        """
        provider_id = self.find_provider_by_name(provider_name)
        if provider_id:
            try:
                url = '{providers_url}/{id}'.format(providers_url=self.providers_url, id=provider_id)
                result = self.client.post(url, action='delete')
                if result['success']:
                    self.changed = True
                    return dict(task_id=result['task_id'], changed=self.changed, msg=result['message'])
                else:
                    return dict(task_id=None, changed=self.changed, api_error=result, msg="Failed to delete {provider_name} provider".format(provider_name=provider_name))
            except Exception as e:
                self.module.fail_json(msg="Failed to delete {provider_name} provider. Error: {error!r}".format(provider_name=provider_name, error=e))
        else:
            return dict(task_id=None, changed=self.changed, msg="Provider {provider_name} doesn't exist".format(provider_name=provider_name))

    def add_or_update_provider(self, provider_name, provider_type, endpoints, zone, provider_region):
        """ Adds a provider to manageiq or update its attributes in case
        a provider with the same name already exists

        Returns:
            the added or updated provider id, whether or not a change took
            place and a short message describing the operation executed,
            including the authentication validation status
        """
        zone_id = self.find_zone_by_name(zone or 'default')
        # check if provider with the same name already exists
        provider_id = self.find_provider_by_name(provider_name)
        if provider_id:  # provider exists
            updates = self.required_updates(provider_id, endpoints, zone_id, provider_region)
            if not updates:
                return dict(changed=self.changed,
                            msg="Provider %s already exists" % provider_name)

            old_validation_details = self.auths_validation_details(provider_id)
            operation = "update"
            self.update_provider(provider_id, provider_name, endpoints, zone_id, provider_region)
            roles_with_changes = set(updates["Added"]) | set(updates["Updated"])
        else:  # provider doesn't exists, adding it to manageiq
            updates = None
            old_validation_details = {}
            operation = "addition"
            provider_id = self.add_new_provider(provider_name, provider_type,
                                                endpoints, zone_id, provider_region)
            roles_with_changes = [e['endpoint']['role'] for e in endpoints]

        authtypes_to_verify = []
        for e in endpoints:
            if e['endpoint']['role'] in roles_with_changes:
                authtypes_to_verify.append(e['authentication']['authtype'])
        result, details = self.verify_authenticaion_validation(provider_id, old_validation_details, authtypes_to_verify)

        if result == "Invalid":
            self.module.fail_json(msg="Failed to Validate provider authentication after {operation}. details: {details}".format(operation=operation, details=details))
        elif result == "Valid":
            self.refresh_provider(provider_id)
            message = "Successful {operation} of {provider} provider. Authentication: {validation}. Refreshing provider inventory".format(operation=operation, provider=provider_name, validation=details)
        elif result == "Timed out":
            message = "Provider {provider} validation after {operation} timed out. Authentication: {validation}".format(operation=operation, provider=provider_name, validation=details)
        return dict(
            provider_id=provider_id,
            changed=self.changed,
            msg=message,
            updates=updates
        )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            zone=dict(required=False, type='str'),
            provider_type=dict(required=True,
                               choices=ManageIQProvider.PROVIDER_TYPES.keys()),
            state=dict(default='present',
                       choices=['present', 'absent']),
            miq_url=dict(default=os.environ.get('MIQ_URL', None)),
            miq_username=dict(default=os.environ.get('MIQ_USERNAME', None)),
            miq_password=dict(default=os.environ.get('MIQ_PASSWORD', None), no_log=True),
            provider_api_port=dict(default=ManageIQProvider.OPENSHIFT_DEFAULT_PORT,
                                   required=False),
            provider_api_hostname=dict(required=False),
            provider_api_auth_token=dict(required=False, no_log=True),
            miq_verify_ssl=dict(require=False, type='bool', default=True),
            ca_bundle_path=dict(required=False, type='str', defualt=None),
            provider_verify_ssl=dict(require=False, type='bool', default=True),
            provider_ca_path=dict(required=False, type='str', defualt=None),
            provider_region=dict(required=False, type='str'),
            access_key_id=dict(required=False, type='str', no_log=True),
            secret_access_key=dict(required=False, type='str', no_log=True),
            metrics=dict(required=False, type='bool', default=False),
            hawkular_hostname=dict(required=False),
            hawkular_port=dict(required=False)
        ),
        required_if=[
            ('provider_type', 'openshift-origin', ['provider_api_hostname', 'provider_api_port', 'provider_api_auth_token']),
            ('provider_type', 'openshift-enterprise', ['provider_api_hostname', 'provider_api_port', 'provider_api_auth_token']),
            ('metrics', True, ['hawkular_hostname', 'hawkular_port']),
            ('provider_type', 'amazon', ['access_key_id', 'secret_access_key', 'provider_region']),
            ('provider_type', 'hawkular-datawarehouse', ['provider_api_hostname', 'provider_api_port', 'provider_api_auth_token'])
        ],
    )

    for arg in ['miq_url', 'miq_username', 'miq_password']:
        if module.params[arg] in (None, ''):
            module.fail_json(msg="missing required argument: {}".format(arg))

    miq_url             = module.params['miq_url']
    miq_username        = module.params['miq_username']
    miq_password        = module.params['miq_password']
    miq_verify_ssl      = module.params['miq_verify_ssl']
    ca_bundle_path      = module.params['ca_bundle_path']
    provider_verify_ssl = module.params['provider_verify_ssl']
    provider_ca_path    = module.params['provider_ca_path']
    provider_name       = module.params['name']
    provider_type       = module.params['provider_type']
    state               = module.params['state']
    zone                = module.params['zone']
    provider_region     = module.params['provider_region']
    access_key_id       = module.params['access_key_id']
    secret_access_key   = module.params['secret_access_key']
    hostname            = module.params['provider_api_hostname']
    port                = module.params['provider_api_port']
    token               = module.params['provider_api_auth_token']
    h_hostname          = module.params['hawkular_hostname']
    h_port              = module.params['hawkular_port']

    manageiq = ManageIQProvider(module, miq_url, miq_username, miq_password, miq_verify_ssl, ca_bundle_path)

    if state == 'present':
        if provider_type in ("openshift-enterprise", "openshift-origin"):
            endpoints = [manageiq.generate_auth_key_config('default', 'bearer', hostname, port, token, provider_verify_ssl, provider_ca_path)]
            if module.params['metrics']:
                endpoints.append(manageiq.generate_auth_key_config('hawkular', 'hawkular', h_hostname, h_port, token, provider_verify_ssl, provider_ca_path))
        elif provider_type == "amazon":
            endpoints = [manageiq.generate_amazon_config('default', 'default', access_key_id, secret_access_key)]
        elif provider_type == "hawkular-datawarehouse":
            endpoints = [manageiq.generate_auth_key_config('default', 'default', hostname, port, token, provider_verify_ssl, provider_ca_path)]

        res_args = manageiq.add_or_update_provider(provider_name,
                                                   provider_type,
                                                   endpoints,
                                                   zone,
                                                   provider_region)
    elif state == 'absent':
        res_args = manageiq.delete_provider(provider_name)

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
