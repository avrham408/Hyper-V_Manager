from infrastructures import wmi_infra
import platform
import wmi
import pytest
from infrastructures import infra_exceptions
import sys

HOST_NAME = platform.uname()[1]


def test_connect_to_wmi():
	HOST_NAME = platform.uname()[1]
	client = wmi_infra.connect_to_wmi(HOST_NAME, r"root\virtualization\v2")
	assert wmi._wmi_namespace == type(client)


def test_connect_to_wmi_where_cimv2():
	HOST_NAME = platform.uname()[1]
	client = wmi_infra.connect_to_wmi(HOST_NAME, r"root\cimv2")
	assert wmi._wmi_namespace == type(client)

def test_connect_to_wmi_failed_when_server_not_exist():
	with pytest.raises(infra_exceptions.ConnectToWmiError): 
		wmi_infra.connect_to_wmi("server_no_exist", "root\virtualization\v2")


def test_connect_to_wmi_failed_when_name_space_not_exist():
	with pytest.raises(infra_exceptions.ConnectToWmiError):
		HOST_NAME = platform.uname()[1]
		wmi_infra.connect_to_wmi(HOST_NAME, "root\virtualizati\v2")


def test_change_vm_state():
	client = wmi_infra.connect_to_wmi(HOST_NAME, r"root\virtualization\v2")
	vms = client.Msvm_ComputerSystem()
	for vm_data in vms:
		vm_name = vm_data.ElementName
		if vm_name.upper() == HOST_NAME.upper():
			continue
		vm = wmi_infra.change_vm_state(client, vm_name, wmi_infra.VmState.Enabled.value)
		assert vm != None
		assert client.Msvm_ComputerSystem(ElementName=vm_name)[0].EnabledState == 2
		wmi_infra.change_vm_state(client, vm_name, wmi_infra.VmState.Disabled.value)
		assert client.Msvm_ComputerSystem(ElementName=vm_name)[0].EnabledState == 3


def test_change__vm_state_for_not_exist_vm():
	client = wmi_infra.connect_to_wmi(HOST_NAME, r"root\virtualization\v2")
	with pytest.raises(infra_exceptions.VmNotFoundError):
		wmi_infra.change_vm_state(client, "blabla", wmi_infra.VmState.Enabled.value)


def test_for_test():
	client = wmi_infra.connect_to_wmi(HOST_NAME, r"root\virtualization\v2")
	for i in wmi_infra.get_vms(client):
		print(i)

if __name__ == "__main__":

	test_for_test()
