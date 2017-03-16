#!/usr/bin/python

import os
from ansible.module_utils.basic import *
from manageiq_client.api import ManageIQClient as MiqApi


DOCUMENTATION = '''
---
module: manageiq_custom_attributes
description: The manageiq_custom_attributes module supports adding, updating and deleting custom attributes on resources in ManageIQ
short_description: add, update, delete an entity custom attributes in ManageIQ
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
  entity_name:
    description:
      - the entity name in manageiq to which the custom attributes belongs
    required: true
    default: null
  entity_type:
    description:
      - the entity type in manageiq to which the custom attributes belongs
    required: true
    default: null
  state:
    description:
      - the state of the custom attributes
      - On present, it will add the custom attributes to the entity if not
        already exist, or update the custom attributes if the associated data
        is different
      - On absent, it will delete the custom attributes from the entity if exist
    required: false
    choices: ['present', 'absent']
    default: 'present'
  custom_attributes:
    description:
      - the custom attributes of the entity
    required: true
    default: null
  miq_verify_ssl:
    description:
      - whether SSL certificates should be verified for HTTPS requests
    required: false
    default: True
    choices: ['True', 'False']
  ca_bundle_path:
    description:
      - the path to a CA_BUNDLE file or directory with certificates
    required: false
    default: null
'''

EXAMPLES = '''
# Add custom attributes for Openshift Containers Provider in ManageIQ
  manageiq_custom_attributes:
    entity_type: 'provider'
    entity_name: 'openshift01'
    state: 'present'
    miq_url: 'http://localhost:3000'
    miq_username: 'admin'
    miq_password: '******'
    custom_attributes:
      - name: "ca1"
        value: "value 1"
      - name: "ca2"
        value: "value 2"
'''


class ManageIQCustomAttributes(object):
    """ ManageIQ object to execute custom attibutes related operations
    in manageiq

    url            - manageiq environment url
    user           - the username in manageiq
    password       - the user password in manageiq
    miq_verify_ssl - whether SSL certificates should be verified for HTTPS requests
    ca_bundle_path - the path to a CA_BUNDLE file or directory with certificates
    """

    supported_entities = {'vm': 'vms', 'provider': 'providers'}

    def __init__(self, module, url, user, password, miq_verify_ssl, ca_bundle_path):
        self.module        = module
        self.api_url       = url + '/api'
        self.user          = user
        self.password      = password
        self.client        = MiqApi(self.api_url, (self.user, self.password), verify_ssl=miq_verify_ssl, ca_bundle_path=ca_bundle_path)
        self.changed       = False

    def find_entity_by_name(self, entity_type, entity_name):
        """ Searches the entity name in ManageIQ.

            Returns:
                the entity id if it exists in manageiq, None otherwise.
        """
        entities_list = getattr(self.client.collections, ManageIQCustomAttributes.supported_entities[entity_type])
        return next((e.id for e in entities_list if e.name == entity_name), None)

    def get_entity_custom_attributes(self, entity_type, entity_id):
        """ Returns the entity's custom attributes
        """
        try:
            url = '{api_url}/{entity_type}/{id}?expand=custom_attributes'.format(
                api_url=self.api_url,
                entity_type=ManageIQCustomAttributes.supported_entities[entity_type],
                id=entity_id)
            result = self.client.get(url)
            return result.get('custom_attributes', [])
        except Exception as e:
            self.module.fail_json(msg="Failed to get {entity_type} custom attributes. Error: {error}".format(
                entity_type=entity_type, error=e))

    def add_custom_attributes(self, entity_type, entity_id, custom_attributes):
        """ Returns the added custom attributes """
        try:
            url = '{api_url}/{entity_type}/{id}/custom_attributes'.format(
                api_url=self.api_url,
                entity_type=ManageIQCustomAttributes.supported_entities[entity_type],
                id=entity_id)
            result = self.client.post(url, action='add', resources=custom_attributes)
            self.changed = True
            return result['results']
        except Exception as e:
            self.module.fail_json(msg="Failed to add the custom attributes. Error: {}".format(e))

    def update_custom_attribute(self, entity_type, entity_id, ca, ca_href):
        """ Returns the updated custom attributes """
        try:
            url = '{api_url}/{entity_type}/{id}/custom_attributes'.format(
                api_url=self.api_url,
                entity_type=ManageIQCustomAttributes.supported_entities[entity_type],
                id=entity_id)
            ca_object = {'name': ca['name'], 'href': ca_href, 'value': ca['value']}
            result = self.client.post(url, action='edit', resources=[ca_object])
            self.changed = True
            return result['results']
        except Exception as e:
            self.module.fail_json(msg="Failed to update the custom attribute {ca_name}. Error: {error}".format(ca_name=ca['name'], error=e))

    @staticmethod
    def compare_custom_attributes(ca1, ca2):
        return (ca1['name'], ca1['section']) == (ca2['name'], ca2['section'])

    def add_or_update_custom_attributes(self, entity_type, entity_name, custom_attributes):
        """ Adds custom attributes to an entity in manageiq or updates the
        attributes in case already exists

        Returns:
            the added or updated custom attributes, whether or not a change
            took place and a short message describing the operation executed
        """
        added, updated = [], []
        message = ""
        # check if entity with the type and name passed exists in manageiq
        entity_id = self.find_entity_by_name(entity_type, entity_name)
        if not entity_id:  # entity doesn't exist
            self.module.fail_json(
                msg="Failed to set the custom attributes. {entity_type} {entity_name} does not exist".format(entity_type=entity_type, entity_name=entity_name))

        entity_cas = self.get_entity_custom_attributes(entity_type, entity_id)
        for new_ca in custom_attributes:
            existing_ca = next((ca for ca in entity_cas if self.compare_custom_attributes(ca, new_ca)), None)
            if existing_ca:
                if new_ca['value'] != existing_ca['value']:
                    updated.extend(self.update_custom_attribute(entity_type, entity_id, new_ca, existing_ca['href']))
            else:
                added.extend(self.add_custom_attributes(entity_type, entity_id, [new_ca]))

        if added or updated:
            message = "Successfully set the custom attributes to {entity_name} {entity_type}"
        else:
            message = "The custom attributes already exist on {entity_name} {entity_type}"

        return dict(
            changed=self.changed,
            msg=message.format(entity_name=entity_name, entity_type=entity_type),
            updates={"Added": added, "Updated": updated}
        )

    def delete_custom_attribute(self, ca, ca_href, entity_type, entity_id):
        """ Returns the deleted custom attribute
        """
        try:
            url = '{api_url}/{entity_type}/{id}/custom_attributes'.format(
                api_url=self.api_url,
                entity_type=ManageIQCustomAttributes.supported_entities[entity_type],
                id=entity_id)
            ca_object = {'name': ca['name'], 'href': ca_href}
            result = self.client.post(url, action='delete', resources=[ca_object])
            self.changed = True
            return result['results']
        except Exception as e:
            self.module.fail_json(msg="Failed to delete the custom attribute {ca}. Error: {error}".format(ca=ca, error=e))

    def delete_custom_attributes(self, entity_type, entity_name, custom_attributes):
        """ Deletes the custom attributes from the entity, if exist

        Returns:
            whether or not a change took and a short message including the
            deleted custom attributes
        """
        deleted = []
        entity_id = self.find_entity_by_name(entity_type, entity_name)
        if not entity_id:  # entity doesn't exist
            self.module.fail_json(
                msg="Failed to delete the custom attributes. {entity_type} {entity_name} does not exist".format(entity_type=entity_type, entity_name=entity_name))

        entity_cas = self.get_entity_custom_attributes(entity_type, entity_id)
        for new_ca in custom_attributes:
            ca_href = next((ca['href'] for ca in entity_cas if self.compare_custom_attributes(ca, new_ca)), None)
            if ca_href:
                deleted.extend(self.delete_custom_attribute(new_ca, ca_href, entity_type, entity_id))

        return dict(
            msg="Successfully deleted the following custom attributes from {entity_name} {entity_type}: {deleted}".format(entity_name=entity_name, entity_type=entity_type, deleted=deleted),
            changed=self.changed
        )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            entity_name=dict(required=True, type='str'),
            entity_type=dict(required=True, type='str',
                             choices=['provider', 'vm']),
            state=dict(default='present',
                       choices=['present', 'absent']),
            custom_attributes=dict(required=True, type='list'),
            miq_url=dict(default=os.environ.get('MIQ_URL', None)),
            miq_username=dict(default=os.environ.get('MIQ_USERNAME', None)),
            miq_password=dict(default=os.environ.get('MIQ_PASSWORD', None), no_log=True),
            miq_verify_ssl=dict(require=False, type='bool', default=True),
            ca_bundle_path=dict(required=False, type='str', defualt=None),
        )
    )

    for arg in ['miq_url', 'miq_username', 'miq_password']:
        if module.params[arg] in (None, ''):
            module.fail_json(msg="missing required argument: {}".format(arg))

    miq_url           = module.params['miq_url']
    miq_username      = module.params['miq_username']
    miq_password      = module.params['miq_password']
    entity_name       = module.params['entity_name']
    entity_type       = module.params['entity_type']
    state             = module.params['state']
    custom_attributes = module.params['custom_attributes']
    miq_verify_ssl    = module.params['miq_verify_ssl']
    ca_bundle_path    = module.params['ca_bundle_path']

    for ca in custom_attributes:
        if 'section' not in ca:
            ca['section'] = 'metadata'

    manageiq = ManageIQCustomAttributes(module, miq_url, miq_username, miq_password, miq_verify_ssl, ca_bundle_path)
    if state == 'present':
        res_args = manageiq.add_or_update_custom_attributes(entity_type, entity_name,
                                                            custom_attributes)
    elif state == 'absent':
        res_args = manageiq.delete_custom_attributes(entity_type, entity_name,
                                                     custom_attributes)
    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
