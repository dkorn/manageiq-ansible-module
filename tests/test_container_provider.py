import pytest
from mock import Mock

from ansible.module_utils.basic import AnsibleModule

from miqclient.api import API
import manageiq


@pytest.fixture(autouse=True)
def miq_api_class(monkeypatch):
    miq_api_class = Mock(spec=API)
    monkeypatch.setattr("manageiq.MiqApi", miq_api_class)
    yield miq_api_class


@pytest.fixture
def the_provider():
    the_provider = Mock()
    the_provider.name = "The provider"
    yield the_provider


@pytest.fixture
def miq_ansible_module():
    miq_ansible_module = Mock(spec=AnsibleModule)
    yield miq_ansible_module


@pytest.fixture
def endpoints(miq):
    endpoints = [miq.generate_endpoint("default", "The hostname", "12345",
                                       "bearer", "The token"),
                 miq.generate_endpoint("hawkular", "The HHostname", "54321",
                                       "hawkular", "The token")]
    yield endpoints


class AnsibleModuleFailed(Exception):
    pass


@pytest.fixture()
def miq(miq_api_class, miq_ansible_module, the_provider):
    def fail(msg):
        raise AnsibleModuleFailed(msg)

    miq_ansible_module.fail_json = fail
    miq = manageiq.ManageIQ(miq_ansible_module, "http://themanageiq.tld",
                            "The username", "The password")

    miq_api_class.return_value.post.return_value = dict(results=[dict(id=0)])
    miq_api_class.return_value.get.return_value = dict(endpoints=[
        {'port': '12345', 'role': 'default', 'hostname': 'The hostname'}])
    miq_api_class.return_value.collections.providers = [the_provider]

    yield miq


def test_generate_endpoint(miq):
    endpoint = miq.generate_endpoint("default", "The hostname", "12345",
                                     "bearer", "The token")
    assert endpoint == {'authentication': {'auth_key': 'The token',
                                           'role': 'bearer'},
                        'endpoint': {'hostname': 'The hostname',
                                     'port': '12345',
                                     'role': 'default'}}


def test_will_add_provider_if_none_present(miq, endpoints):
    miq.client.collections.providers = []
    res_args = miq.add_or_update_provider(
        "The provider", "openshift-origin", endpoints)
    assert res_args == {'changed': True,
                        'msg': 'Successfuly added The provider provider',
                        'provider_id': 0}
    miq.client.post.assert_called_once_with(
        'http://themanageiq.tld/api/providers',
        connection_configurations=[
            {'endpoint': {'port': '12345',
                          'role': 'default',
                          'hostname': 'The hostname'},
             'authentication': {'auth_key': 'The token', 'role': 'bearer'}},
            {'endpoint': {'port': '54321', 'role': 'hawkular',
                          'hostname': 'The HHostname'},
             'authentication': {'auth_key': 'The token', 'role': 'hawkular'}}],
        name='The provider',
        type='ManageIQ::Providers::Openshift::ContainerManager')


def test_will_update_provider_if_present(miq, endpoints, the_provider):
    res_args = miq.add_or_update_provider(
        "The provider", "openshift-origin", endpoints)
    assert res_args == {'changed': True,
                        'msg': 'Successfuly updated The provider provider',
                        'provider_id': the_provider.id}


def test_reports_error(miq, endpoints, the_provider, miq_api_class):
    miq_api_class().get.side_effect = Exception("foo")
    with pytest.raises(AnsibleModuleFailed) as excinfo:
        miq.add_or_update_provider(
            "The provider", "openshift-origin", endpoints)
    assert str(excinfo.value) == "Failed to get provider data. Error: foo"
