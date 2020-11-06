from infrastructures import wmi_infra
import platform
import wmi
import pytest
from infrastructures import infra_exceptions

def test_connect_to_wmi():
	host_name = platform.uname()[1]
	client = wmi_infra.connect_to_wmi(host_name, r"root\virtualization\v2")
	assert wmi._wmi_namespace == type(client)


def test_connect_to_wmi_where_cimv2():
	host_name = platform.uname()[1]
	client = wmi_infra.connect_to_wmi(host_name, r"root\cimv2")
	assert wmi._wmi_namespace == type(client)

def test_connect_to_wmi_failed_when_server_not_exist():
	with pytest.raises(infra_exceptions.ConnectToWmiError): 
		wmi_infra.connect_to_wmi("server_no_exist", "root\virtualization\v2")


def test_connect_to_wmi_failed_when_name_space_not_exist():
	with pytest.raises(infra_exceptions.ConnectToWmiError):
		host_name = platform.uname()[1]
		wmi_infra.connect_to_wmi(host_name, "root\virtualizati\v2")


def test_change_vm_state_when_state_turn_on():
	host_name = platform.uname()[1]
	client = wmi_infra.connect_to_wmi(host_name, r"root\virtualization\v2")
	wmi_infra.change_vm_state(client, "2004 enterprise", wmi_infra.VmState.Enabled.value)


def test_change_vm_state_when_state_turn_off():
	host_name = platform.uname()[1]
	client = wmi_infra.connect_to_wmi(host_name, r"root\virtualization\v2")
	wmi_infra.change_vm_state(client, "2004 enterprise", wmi_infra.VmState.Disabled.value)





if __name__ == "__main__":
	test_change_vm_state_when_state_turn_on()
	test_change_vm_state_when_state_turn_off()