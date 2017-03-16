#!/usr/bin/python


DOCUMENTATION = '''
---
module: manageiq_user
description: The manageiq_user module supports adding, updating and deleting users in ManageIQ.
short_description: management of users in ManageIQ
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
  name:
    description:
      - the unique userid in manageiq, often mentioned as username
    required: true
    default: null
  fullname:
    description:
      - the users' full name
    required: false
    default: null
  password:
    description:
      - the users' password
    required: false
    default: null
  group:
    description:
      - the name of the group to which the user belongs
    required: false
    default: null
  email:
    description:
      - the users' E-mail address
    required: false
    default: null
  state:
    description:
      - the state of the user
      - On present, it will create the user if it does not exist or update the
        user if the associated data is different
      - On absent, it will delete the user if it exists
    required: false
    choices: ['present', 'absent']
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
# Create a new user in ManageIQ
  manageiq_user:
    name: 'dkorn'
    fullname: 'Daniel Korn'
    password: '******'
    group: 'EvmGroup-user'
    email: 'dkorn@redhat.com'
    state: 'present'
    miq_url: 'http://localhost:3000'
    miq_username: 'admin'
    miq_password: '******'
    miq_verify_ssl: False
'''

import os
from manageiq_client.api import ManageIQClient as MiqApi


class ManageIQUser(object):
    """ ManageIQ object to execute user management operations in manageiq

    url            - manageiq environment url
    user           - the username in manageiq
    password       - the user password in manageiq
    miq_verify_ssl - whether SSL certificates should be verified for HTTPS requests
    ca_bundle_path - the path to a CA_BUNDLE file or directory with certificates
    """

    def __init__(self, module, url, user, password, miq_verify_ssl, ca_bundle_path):
        self.module        = module
        self.api_url       = url + '/api'
        self.user          = user
        self.password      = password
        self.client        = MiqApi(self.api_url, (self.user, self.password), verify_ssl=miq_verify_ssl, ca_bundle_path=ca_bundle_path)
        self.changed       = False

    def find_group_by_name(self, group_name):
        """ Searches the group name in ManageIQ.

        Returns:
            the group id if it exists in manageiq, None otherwise.
        """
        groups = self.client.collections.groups
        return next((group.id for group in groups if group.description == group_name), None)

    def find_user_by_userid(self, userid):
        """ Searches the userid in ManageIQ.

        Returns:
            the user's id if it exists in manageiq, None otherwise.
        """
        users = self.client.collections.users
        return next((user.id for user in users if user.userid == userid), None)

    def delete_user(self, userid):
        """Deletes the user from manageiq.

        Returns:
            a short message describing the operation executed.
        """
        user_id = self.find_user_by_userid(userid)
        if not user_id:  # user doesn't exist
            return dict(
                changed=self.changed,
                msg="User {userid} does not exist in manageiq".format(userid=userid))
        try:
            url = '{api_url}/users/{user_id}'.format(api_url=self.api_url, user_id=user_id)
            result = self.client.post(url, action='delete')
            self.changed = True
            return dict(changed=self.changed, msg=result['message'])
        except Exception as e:
            self.module.fail_json(msg="Failed to delete user {userid}: {error}".format(userid=userid, error=e))

    def user_update_required(self, user_id, userid, username, group_id, email):
        """ Returns true if the username, group id or email passed for the user
            differ from the user's existing ones, False otherwise.
        """
        try:
            url = "{api_url}/users/{user_id}".format(api_url=self.api_url, user_id=user_id)
            result = self.client.get(url)
            return result['name'] != username or result['current_group_id'] != group_id or result.get('email') != email
        except Exception as e:
            self.module.fail_json(msg="Failed to get user {userid} details. Error: {error}".format(userid=userid, error=e))

    def update_user_if_required(self, user_id, userid, username, group_id, password, email):
        """Updates the user in manageiq.

        Returns:
            the created user id, name, created_on timestamp,
            updated_on timestamp, userid and current_group_id
        """
        if not self.user_update_required(user_id, userid, username, group_id, email):
            return dict(
                changed=self.changed,
                msg="User {userid} already exist, no need for updates".format(userid=userid))
        try:
            url = '{api_url}/users/{user_id}'.format(api_url=self.api_url, user_id=user_id)
            resource = {'userid': userid, 'name': username, 'password': password,
                        'group': {'id': group_id}, 'email': email}
            result = self.client.post(url, action='edit', resource=resource)
            self.changed = True
            return dict(
                changed=self.changed,
                msg="Successfully updated the user {userid}: {user_details}".format(userid=userid, user_details=result))
        except Exception as e:
            self.module.fail_json(msg="Failed to update user {userid}: {error}".format(userid=userid, error=e))

    def create_user(self, userid, username, group_id, password, email):
        """Creates the user in manageiq.

        Returns:
            the created user id, name, created_on timestamp,
            updated_on timestamp, userid and current_group_id
        """
        try:
            url = '{api_url}/users'.format(api_url=self.api_url)
            resource = {'userid': userid, 'name': username, 'password': password,
                        'group': {'id': group_id}, 'email': email}
            result = self.client.post(url, action='create', resource=resource)
            self.changed = True
            return dict(
                changed=self.changed,
                msg="Successfully created the user {userid}: {user_details}".format(userid=userid, user_details=result['results']))
        except Exception as e:
            self.module.fail_json(msg="Failed to create user {userid}: {error}".format(userid=userid, error=e))

    def create_or_update_user(self, userid, username, password, group, email):
        """ Create or update a user in manageiq.

        Returns:
            Whether or not a change took place and a message describing the
            operation executed.
        """
        group_id = self.find_group_by_name(group)
        if not group_id:  # group doesn't exist
            self.module.fail_json(
                msg="Failed to create user {userid}: group {group_name} does not exist in manageiq".format(userid=userid, group_name=group))

        user_id = self.find_user_by_userid(userid)
        if user_id:  # user already exist
            return self.update_user_if_required(user_id, userid, username, group_id, password, email)
        else:
            return self.create_user(userid, username, group_id, password, email)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
            fullname=dict(required=False, type='str'),
            password=dict(required=False, type='str', no_log=True),
            group=dict(required=False, type='str'),
            email=dict(required=False, type='str'),
            state=dict(required=True, type='str',
                       choices=['present', 'absent']),
            miq_url=dict(default=os.environ.get('MIQ_URL', None)),
            miq_username=dict(default=os.environ.get('MIQ_USERNAME', None)),
            miq_password=dict(default=os.environ.get('MIQ_PASSWORD', None), no_log=True),
            miq_verify_ssl=dict(require=False, type='bool', default=True),
            ca_bundle_path=dict(required=False, type='str', defualt=None)
        ),
        required_if=[
            ('state', 'present', ['fullname', 'group', 'password'])
        ],
    )

    for arg in ['miq_url', 'miq_username', 'miq_password']:
        if module.params[arg] in (None, ''):
            module.fail_json(msg="missing required argument: {}".format(arg))

    miq_url        = module.params['miq_url']
    miq_username   = module.params['miq_username']
    miq_password   = module.params['miq_password']
    miq_verify_ssl = module.params['miq_verify_ssl']
    ca_bundle_path = module.params['ca_bundle_path']
    name           = module.params['name']
    fullname       = module.params['fullname']
    password       = module.params['password']
    group          = module.params['group']
    email          = module.params['email']
    state          = module.params['state']

    manageiq = ManageIQUser(module, miq_url, miq_username, miq_password, miq_verify_ssl, ca_bundle_path)
    if state == "present":
        res_args = manageiq.create_or_update_user(name, fullname, password,
                                                  group, email)
    if state == "absent":
        res_args = manageiq.delete_user(name)

    module.exit_json(**res_args)


# Import module bits
from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
