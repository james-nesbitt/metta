import pytest

# imports used only for type testing
from mirantis.testing.metta_dummy.provisioner import DummyProvisionerPlugin
from mirantis.testing.metta_dummy.client import DummyClientPlugin
from mirantis.testing.metta_dummy.workload import DummyWorkloadPlugin


def test_provisioner_workflow(provisioner):
    """ test that the provisioner can follow a decent workflow """

    provisioner.prepare()
    provisioner.apply()

    # ...

    provisioner.destroy()


def test_workloads_outputs(workloads):
    """ test that the dummy workload got its outputs from configuration """
    workload_two = workloads.get_plugin(instance_id='work2')

    assert workload_two.get_output(
        instance_id='output1').get_output() == "workload two dummy output one"


def test_provisioner_outputs(provisioner):
    """ test that the provisioner produces the needed clients """
    # check that we can get an output from a provisioner
    provisioner_output_dummy = provisioner.get_output(instance_id='output1')
    assert provisioner_output_dummy.get_output() == "prov dummy output one"

    # make sure that an error is raised if the key doesn't exist
    with pytest.raises(KeyError):
        provisioner.get_output(instance_id='does not exist')


def test_provisioner_clients(provisioner):
    """ test that the provisioner produces the needed clients """

    # two ways to get the same client in this case
    client_one = provisioner.get_client(instance_id='client1')
    assert isinstance(client_one, DummyClientPlugin)
    assert client_one.instance_id == 'client1'
    client_dummy = provisioner.get_client(plugin_id='dummy')
    assert isinstance(client_dummy, DummyClientPlugin)
    assert client_dummy.instance_id == 'client1'

    # make sure that an error is raised if the key doesn't exist
    with pytest.raises(KeyError):
        provisioner.get_client(plugin_id='does not exist')


def test_client_outputs(provisioner):
    """ test that the provisioner clients behave like clients """

    client_one = provisioner.get_client(instance_id='client1')
    assert isinstance(client_one, DummyClientPlugin)

    # test that the dummy plugin can load a text output
    client_one_output = client_one.get_output(instance_id='output1')
    assert client_one_output.get_output() == "prov client one output one"

    # test that the dummy plugin can load a dict output
    client_two_output = client_one.get_output(instance_id='output2')
    # Test dict as a loaded config plugin
    assert client_two_output.get_output(
        '1.1') == "prov client one output two data one.one"
