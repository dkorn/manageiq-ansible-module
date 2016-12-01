**Work in progress**

Brings up ManageIQ and OpenShift in containers, configures permissions on OpenShift side, fetches access token, and adds the provider in ManageIQ.

For `docker_container` ansible module you might need to:

    pip install docker-py

`./openshift-ansible` subdir here is a git submodule, you might need to:

    git submodule update --init

Usage:

    ansible-playbook ./miq_with_openshift.yml

Can choose [ManageIQ version][1] and [Openshift version][2]:

    ansible-playbook ./miq_with_openshift.yml --extra-vars 'miq_version=latest-euwe openshift_version=v1.3.1`

[1]: https://hub.docker.com/r/manageiq/manageiq/tags/
[2]: https://hub.docker.com/r/openshift/origin/tags/

Can also use other `miq_image`, `openshift_image`.
