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
	vms = client.Msvm_ComputerSystem(Description = "Microsoft Virtual Machine")
	for vm_data in vms:
		vm_name = vm_data.ElementName
		vm = wmi_infra.change_vm_state(client, vm_name, wmi_infra.VmState.Enabled.value)
		assert vm != None
		assert client.Msvm_ComputerSystem(ElementName=vm_name)[0].EnabledState == 2
		wmi_infra.change_vm_state(client, vm_name, wmi_infra.VmState.Disabled.value)
		assert client.Msvm_ComputerSystem(ElementName=vm_name)[0].EnabledState == 3


def test_change__vm_state_for_not_exist_vm():
	client = wmi_infra.connect_to_wmi(HOST_NAME, r"root\virtualization\v2")
	with pytest.raises(infra_exceptions.VmNotFoundError):
		wmi_infra.change_vm_state(client, "blabla", wmi_infra.VmState.Enabled.value)


def test_get_vms_all_vms_types():
	client = wmi_infra.connect_to_wmi(HOST_NAME, r"root\virtualization\v2")
	vms = client.Msvm_ComputerSystem()
	for vm in wmi_infra.get_vms(client):
		#Todo 
		print(vm["name"])


def test_set_vm_memory():
	client = wmi_infra.connect_to_wmi(HOST_NAME, r"root\virtualization\v2")
	wmi_infra.set_vm_memory(client, "202H", 5000)
	#Todo add assert


def test_set_vm_service():
	client = wmi_infra.connect_to_wmi(HOST_NAME, r"root\virtualization\v2")
	vms = client.Msvm_ComputerSystem(Description = "Microsoft Virtual Machine")
	for vm in vms:
		statuses = wmi_infra.get_services_status(client, vm.ElementName)
		for service_name, status  in statuses.items():
			new_status = False if status else True
			wmi_infra.set_vm_service(client, vm.ElementName, service_name, new_status)
			assert status != wmi_infra.get_service_status(client, vm.ElementName, service_name)


def test_set_all_services_on():
	client = wmi_infra.connect_to_wmi(HOST_NAME, r"root\virtualization\v2")
	vms = client.Msvm_ComputerSystem(Description = "Microsoft Virtual Machine")
	for vm in vms:
		statuses = wmi_infra.get_services_status(client, vm.ElementName)
		for service_name in statuses:
			wmi_infra.set_vm_service(client, vm.ElementName, service_name, False)
		wmi_infra.set_all_services_on(client, vm.ElementName)
		new_statuses = wmi_infra.get_services_status(client, vm.ElementName)
		for _, status in new_statuses.items():
			assert status is True
		

if __name__ == "__main__":
	test_set_all_services_on()
