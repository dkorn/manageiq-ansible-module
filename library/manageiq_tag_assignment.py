#!/usr/bin/python

import os
from ansible.module_utils.basic import *
from manageiq_client.api import ManageIQClient as MiqApi


DOCUMENTATION = '''
---
module: manageiq_tag_assignment
short_description: assign and unassign tags on resources in ManageIQ
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
  tags:
    description:
      - list of dictionaries representing tags, each includes 'name' (tag name) and 'category' (category name) keys
      - categories have a 'single_value': True/False. assigning a tag in a single_value: True category
        clears other tags from that category.
    required: true
    default: null
  resource:
    description:
      - the relevant resource type in manageiq
    required: true
    choices: ['provider', 'host', 'vm', 'blueprint', 'category', 'cluster', 'data store', 'group', 'resource pool', 'service', 'service template', 'template', 'tenant', 'user']
    default: null
  resource_name:
    description:
      - the relevant resource name in manageiq
    required: true
    default: null
  state:
    description:
      - On present, it will assign the tag on the resource, if not already assigned
      - On absent, it will unassign the tag from the resource
    required: true
    choices: ['present', 'absent']
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
# Assign tag on a provider in ManageIQ
  manageiq_tag_assignment:
    tags:
    - category: environment
      name: prod
    - category: owner
      name: prod_ops
    resource_name: 'OpenShift01'
    resource: 'provider'
    state: 'present'
    miq_url: 'http://localhost:3000'
    miq_username: 'admin'
    miq_password: '******'
'''


class ManageIQTagAssignment(object):
    """ ManageIQ object to execute tag assignments in manageiq

    url            - manageiq environment url
    user           - the username in manageiq
    password       - the user password in manageiq
    miq_verify_ssl - whether SSL certificates should be verified for HTTPS requests
    ca_bundle_path - the path to a CA_BUNDLE file or directory with certificates
    """

    manageiq_entities = {
        'provider': 'providers', 'host': 'hosts', 'vm': 'vms',
        'category': 'categories', 'cluster': 'clusters', 'data store': 'data_stores',
        'group': 'groups', 'resource pool': 'resource_pools', 'service': 'services',
        'service template': 'service_templates', 'template': 'templates',
        'tenant': 'tenants', 'user': 'users', 'blueprint': 'blueprints'
    }
    actions = {'present': 'assign', 'absent': 'unassign'}

    def __init__(self, module, url, user, password, miq_verify_ssl, ca_bundle_path):
        self.module   = module
        self.api_url  = url + '/api'
        self.user     = user
        self.password = password
        self.client   = MiqApi(self.api_url, (self.user, self.password), verify_ssl=miq_verify_ssl, ca_bundle_path=ca_bundle_path)
        self.changed  = False

    def find_entity_by_name(self, entity_type, entity_name):
        """ Searches the entity name in ManageIQ.

        Returns:
            the entity id if it exists in manageiq, None otherwise.
        """
        entities_list = getattr(self.client.collections, entity_type)
        return next((e.id for e in entities_list if e.name == entity_name), None)

    def query_resource_tags(self, resource_type, resource_id):
        """ Returns a set of the full tag names assigned to the resource
        """
        try:
            url = '{api_url}/{resource_type}/{resource_id}/tags?expand=resources'.format(api_url=self.api_url, resource_type=resource_type, resource_id=resource_id)
            response = self.client.get(url)
        except Exception as e:
            self.module.fail_json(msg="Failed to query {resource_type} tags: {error}".format(resource_type=resource_type, error=e))
        tags = response.get('resources', [])
        tags_set = set([tag['name'] for tag in tags])
        return tags_set

    def execute_action(self, resource_type, resource_id, tags, action):
        """Executes the action for the resource tag
        """
        url = '{api_url}/{resource_type}/{resource_id}/tags'.format(api_url=self.api_url, resource_type=resource_type, resource_id=resource_id)
        try:
            response = self.client.post(url, action=action, resources=tags)
        except Exception as e:
            self.module.fail_json(msg="Failed to {action} tag: {error}".format(action=action, error=e))
        for result in response['results']:
            if result['success']:
                self.changed = True
            else:
                self.module.fail_json(msg="Failed to {action}: {fail_message}".format(action=action, entity=entity, fail_message=result['message']))

    def full_tag_name(self, tag):
        """ Returns the full tag name in manageiq
        """
        full_tag_name = '/managed/{category_name}/{tag_name}'.format(category_name=tag['category'], tag_name=tag['name'])
        return full_tag_name

    def assign_or_unassign_tag(self, tags, resource, resource_name, state):
        """ Assign or unassign the tag on a manageiq resource.

        Returns:
            Whether or not a change took place and a message describing the
            operation executed.
        """
        resource_type = self.manageiq_entities[resource]
        resource_id = self.find_entity_by_name(resource_type, resource_name)
        if not resource_id:  # resource doesn't exist
            self.module.fail_json(
                msg="Failed to {action} tag: {resource_name} {resource} does not exist in manageiq".format(
                    action=ManageIQTagAssignment.actions[state],
                    resource_name=resource_name, resource=resource))

        tags_to_execute = []
        assigned_tags = self.query_resource_tags(resource_type, resource_id)
        for tag in tags:
            assigned = self.full_tag_name(tag) in assigned_tags

            if assigned and state == 'absent':
                tags_to_execute.append(tag)
            elif (not assigned) and state == 'present':
                tags_to_execute.append(tag)

        if not tags_to_execute:
            return dict(
                changed=self.changed,
                msg="tags alraedy {action}ed, nothing to do".format(action=ManageIQTagAssignment.actions[state]))
        else:
            self.execute_action(resource_type, resource_id, tags_to_execute, ManageIQTagAssignment.actions[state])
            return dict(
                changed=self.changed,
                msg="Successfully {action}ed tags".format(action=ManageIQTagAssignment.actions[state]))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            tags=dict(required=True, type='list'),
            resource_name=dict(required=True, type='str'),
            resource=dict(required=True, type='str',
                          choices=['provider', 'host', 'vm', 'blueprint', 'category',
                                   'cluster', 'data store', 'group', 'resource pool',
                                   'service', 'service template', 'template', 'tenant',
                                   'user']),
            state=dict(required=True, type='str',
                       choices=['present', 'absent']),
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

    miq_url        = module.params['miq_url']
    miq_username   = module.params['miq_username']
    miq_password   = module.params['miq_password']
    tags           = module.params['tags']
    resource       = module.params['resource']
    resource_name  = module.params['resource_name']
    state          = module.params['state']
    miq_verify_ssl = module.params['miq_verify_ssl']
    ca_bundle_path = module.params['ca_bundle_path']

    manageiq = ManageIQTagAssignment(module, miq_url, miq_username, miq_password, miq_verify_ssl, ca_bundle_path)
    res_args = manageiq.assign_or_unassign_tag(tags, resource, resource_name, state)

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
