# -*- coding: utf-8 -*-
import pytest
from mock import Mock

from ansible.module_utils.basic import AnsibleModule

from manageiq_client.api import ManageIQClient
import manageiq_tag_assignment


TAG_NAME = "tag01"
CATEGORY_NAME = "cat01"
PROVIDER_NAME = "provider01"
MANAGEIQ_HOSTNAME = "http://themanageiq.tld"


@pytest.fixture(autouse=True)
def miq_api_class(monkeypatch):
    miq_api_class = Mock(spec=ManageIQClient)
    monkeypatch.setattr("manageiq_tag_assignment.MiqApi", miq_api_class)
    yield miq_api_class


@pytest.fixture
def the_provider():
    the_provider = Mock()
    the_provider.name = PROVIDER_NAME
    the_provider.id = 1
    yield the_provider


@pytest.fixture
def miq_ansible_module():
    miq_ansible_module = Mock(spec=AnsibleModule)
    yield miq_ansible_module


class AnsibleModuleFailed(Exception):
    pass


@pytest.fixture()
def miq(miq_api_class, miq_ansible_module, the_provider):
    def fail(msg):
        raise AnsibleModuleFailed(msg)

    miq_ansible_module.fail_json = fail
    miq = manageiq_tag_assignment.ManageIQTagAssignment(
        miq_ansible_module, MANAGEIQ_HOSTNAME, "The username",
        "The password", miq_verify_ssl=False, ca_bundle_path=None)

    miq_api_class.return_value.post.return_value = dict(results=[
        {"success": True,
         "message": "Assigning Tag: category:'environment' name:'dev'",
         "href": "http://localhost:3000/api/providers/1",
         "tag_category": "environment",
         "tag_name": "dev"}])
    miq_api_class.return_value.get.return_value = dict(resources=[
        {"href": "http://localhost:3000/api/providers/27/tags/1",
         "id": 1,
         "name": "/managed/environment/dev"}])
    miq_api_class.return_value.collections.providers = [the_provider]
    yield miq


def will_try_to_assign_tag_when_allready_assigned(miq, miq_api_class, the_provider):
    res_args = miq.assign_or_unassign_tag(
        [{'name': TAG_NAME, 'category': CATEGORY_NAME}],
        'provider', PROVIDER_NAME, 'present')
    assert res_args == {
        "changed": False,
        "msg": "Tags allready assigned, tothing to do"}


def test_will_assign_tag_on_resource_if_not_assigned(miq, miq_api_class, the_provider):
    miq_api_class.return_value.get.return_value = {}
    res_args = miq.assign_or_unassign_tag(
        [{'name': TAG_NAME, 'category': CATEGORY_NAME}],
        'provider', PROVIDER_NAME, 'present')
    assert res_args == {
        "changed": True,
        "msg": "Successfully assigned tags"}
    miq.client.post.assert_called_once_with(
        '{}/api/providers/1/tags'.format(MANAGEIQ_HOSTNAME),
        action='assign', resources=[{'name': TAG_NAME, 'category': CATEGORY_NAME}])

