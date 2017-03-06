# -*- coding: utf-8 -*-
import pytest
from mock import Mock

from ansible.module_utils.basic import AnsibleModule

from manageiq_client.api import ManageIQClient
import manageiq_policy_assignment


POLICY_PROFILE_NAME = "profile01"
RESOURCE_NAME = "provider01"
MANAGEIQ_HOSTNAME = "http://themanageiq.tld"


@pytest.fixture(autouse=True)
def miq_api_class(monkeypatch):
    miq_api_class = Mock(spec=ManageIQClient)
    monkeypatch.setattr("manageiq_policy_assignment.MiqApi", miq_api_class)
    yield miq_api_class


@pytest.fixture
def the_provider():
    the_provider = Mock()
    the_provider.name = RESOURCE_NAME
    the_provider.id = 1
    yield the_provider


@pytest.fixture
def the_policy_profile():
    the_policy_profile = Mock()
    the_policy_profile.name = POLICY_PROFILE_NAME
    the_policy_profile.id = 1
    the_policy_profile.guid = '0bf2e43a-1211-11e6-aa9c-02424d459b45'
    the_policy_profile.description = "test policy profile"
    yield the_policy_profile


@pytest.fixture
def miq_ansible_module():
    miq_ansible_module = Mock(spec=AnsibleModule)
    yield miq_ansible_module


class AnsibleModuleFailed(Exception):
    pass


@pytest.fixture()
def miq(miq_api_class, miq_ansible_module, the_policy_profile, the_provider):
    def fail(msg):
        raise AnsibleModuleFailed(msg)

    miq_ansible_module.fail_json = fail
    miq = manageiq_policy_assignment.ManageIQ(
            miq_ansible_module, MANAGEIQ_HOSTNAME, "The username",
            "The password", miq_verify_ssl=False, ca_bundle_path=None)

    miq_api_class.return_value.post.return_value = dict(results=[
        {"success": True,
         "message": "Assigning Policy Profile: id:'1' description:'test policy profile' guid:'0bf2e43a-1211-11e6-aa9c-02424d459b45'",
         "href": "http://localhost:3000/api/providers/1",
         "policy_profile_id": 1,
         "policy_profile_href": "http://localhost:3000/api/policy_profiles/1"}])
    miq_api_class.return_value.get.return_value = dict(resources=[
        {"href": "http://localhost:3000/api/providers/1/policy_profiles/1",
         "id": 1,
         "name": "profile01",
         "description": "test policy profile",
         "set_type": "MiqPolicySet",
         "guid": "0bf2e43a-1211-11e6-aa9c-02424d459b45"}])
    miq_api_class.return_value.collections.providers = [the_provider]
    miq_api_class.return_value.collections.policy_profiles = [the_policy_profile]

    yield miq


def test_will_assign_policy_profile_on_resource_if_not_assigned(miq, miq_api_class, the_policy_profile, the_provider):
    miq_api_class.return_value.get.return_value = {}
    res_args = miq.assign_or_unassign_entity(
        'policy profile', POLICY_PROFILE_NAME, 'provider', RESOURCE_NAME, 'present')
    assert res_args == {
            "changed": True,
            "msg": "Assigning Policy Profile: id:'{id}' description:'test policy profile' guid:'{guid}'".format(
                id=the_policy_profile.id, guid=the_policy_profile.guid)}
    miq.client.post.assert_called_once_with(
        '{}/api/providers/1/policy_profiles'.format(MANAGEIQ_HOSTNAME),
        action='assign', resource={"href": "{}/api/policy_profiles/1".format(MANAGEIQ_HOSTNAME)})
