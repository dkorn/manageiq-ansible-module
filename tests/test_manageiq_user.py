# -*- coding: utf-8 -*-
import pytest
from mock import Mock

from ansible.module_utils.basic import AnsibleModule

from manageiq_client.api import ManageIQClient
import manageiq_user


MANAGEIQ_HOSTNAME = "http://miq.example.com"
USERID = "testuser"
MANGEIQ_USER_ID = "15"
USERNAME = "Test User"
PASSWORD = "123"
GROUP = "Test Group"
GROUP_ID = "5"
EMAIL = "testuser@example.com"


GET_RETURN_VALUES = {
    'user_not_exist': {},
    'user_exist': {
        "id": MANGEIQ_USER_ID,
        "name": USERNAME,
        "created_on": "2016-11-17T08:33:24Z",
        "updated_on": "2016-11-17T08:56:55Z",
        "userid": USERID,
        "email": EMAIL,
        "current_group_id": GROUP_ID
    }
}

POST_RETURN_VALUES = {
    'created_user': {
        'name': USERNAME,
        'userid': USERID,
        'current_group_id': GROUP_ID,
        'created_on': '2016-11-17T08:33:24Z',
        'updated_on': u'2016-11-17T08:56:55Z',
        'id': MANGEIQ_USER_ID,
        'email': EMAIL
    },
    'updated_user': {
        'name': "New Name",
        'userid': USERID,
        'current_group_id': GROUP_ID,
        'created_on': '2016-11-17T08:33:24Z',
        'updated_on': u'2016-11-17T08:56:55Z',
        'id': MANGEIQ_USER_ID,
        'email': "newname@example.com"
    },
    'deleted_user': {
        'success': 'true',
        'message': "users id: 15 deleting",
    }
}


@pytest.fixture()
def the_user():
    the_user = Mock()
    the_user.userid = USERID
    the_user.username = USERNAME
    the_user.email = EMAIL
    the_user.password = PASSWORD
    yield the_user


@pytest.fixture()
def the_group():
    the_group = Mock()
    the_group.id = GROUP_ID
    the_group.description = GROUP
    yield the_group


@pytest.fixture(autouse=True)
def miq_api_class(monkeypatch):
    miq_api_class = Mock(spec=ManageIQClient)
    monkeypatch.setattr("manageiq_user.MiqApi", miq_api_class)
    yield miq_api_class


@pytest.fixture
def miq_ansible_module():
    miq_ansible_module = Mock(spec=AnsibleModule)
    yield miq_ansible_module


class AnsibleModuleFailed(Exception):
    pass


@pytest.fixture()
def miq(miq_api_class, miq_ansible_module):

    def fail(msg):
        raise AnsibleModuleFailed(msg)

    miq_ansible_module.fail_json = fail
    miq = manageiq_user.ManageIQUser(
        miq_ansible_module, MANAGEIQ_HOSTNAME, "The username", "The password",
        False, None)

    yield miq


def create_user_if_not_exist(miq, miq_api_class, the_group):
    miq_api_class.return_value.collections.groups = [the_group]
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['user_not_exist']
    miq_api_class.return_value.get.return_value = POST_RETURN_VALUES['created_user']

    result = miq.create_or_update_user(USERID, USERNAME, PASSWORD, GROUP, EMAIL)
    assert result == {
        'changed': True,
        'msg': "Successfully created the user dkorn: {}".format(POST_RETURN_VALUES['created_user'])
    }
    miq.client.post.assert_called_once_with(
        '{hostname}/api/users'.format(hostname=MANAGEIQ_HOSTNAME),
        action='create',
        resource={'userid': USERID, 'name': USERNAME, 'password': PASSWORD, 'group': {'id': GROUP_ID}, 'email': EMAIL}
    )

def update_user_email_and_name(miq, miq_api_class, the_user, the_group):
    miq_api_class.return_value.collections.users = [the_user]
    miq_api_class.return_value.collections.groups = [the_group]
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['user_exist']
    miq_api_class.return_value.get.return_value = POST_RETURN_VALUES['updated_user']

    result = miq.create_or_update_user(USERID, "New Name", PASSWORD, GROUP, "newname@example.com")
    assert result == {
        'changed': True,
        'msg': "Successfully updated the user dkorn: {}".format(POST_RETURN_VALUES['updated_user'])
    }
    miq.client.post.assert_called_once_with(
        '{hostname}/api/users'.format(hostname=MANAGEIQ_HOSTNAME),
        action='update',
        resource={'userid': USERID, 'name': USERNAME, 'password': PASSWORD, 'group': {'id': GROUP_ID}, 'email': EMAIL}
    )


def delete_existing_user(miq, miq_api_class, the_user, the_group):
    miq_api_class.return_value.collections.users = [the_user]
    miq_api_class.return_value.collections.groups = [the_group]
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['user_exist']
    miq_api_class.return_value.get.return_value = POST_RETURN_VALUES['deleted_user']

    result = miq.delete_user(USERID)
    assert result == {
        'changed': True,
        'msg': "users id: 15 deleting"
    }
    miq.client.get.assert_called_once_with(
        '{hostname}/api/users/{userid}'.format(hostname=MANAGEIQ_HOSTNAME, userid=USERID))
    miq.client.post.assert_called_once_with(
        '{hostname}/api/users/{userid}'.format(hostname=MANAGEIQ_HOSTNAME, userid=USERID),
        action='delete')


def test_fail_delete_user_not_exist(miq, miq_api_class):
    miq_api_class.return_value.collections.users = []
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['user_not_exist']

    result = miq.delete_user(USERID)
    assert result == {
        'changed': False,
        'msg': 'User testuser does not exist in manageiq'
    }


def test_fail_create_user_group_not_exist(miq, miq_api_class):
    miq_api_class.return_value.collections.groups = []

    with pytest.raises(AnsibleModuleFailed, message="Failed to create user testuser: group Test Group does not exist in manageiq"):
        miq.create_or_update_user(USERID, USERNAME, PASSWORD, GROUP, EMAIL)


def test_create_user_with_same_attributes(miq, miq_api_class, the_user, the_group):
    miq_api_class.return_value.collections.groups = [the_group]
    miq_api_class.return_value.collections.users = [the_user]
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['user_exist']

    result = miq.create_or_update_user(USERID, USERNAME, PASSWORD, GROUP, EMAIL)
    assert result == {
        'changed': False,
        'msg': 'User testuser already exist, no need for updates'
    }
