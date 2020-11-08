import wmi 
from enum import Enum
import pywintypes
from infrastructures import infra_exceptions
import time
import datetime
import platform
import logging
from infrastructures import log_config

HOST_NAME = platform.uname()[1]
logger = logging.getLogger(__name__)

class VmState(Enum):
	Other = 1                    
	Enabled = 2                  
	Disabled = 3                 
	ShutDown = 4                 
	Offline = 6                  
	Test = 7                     
	Defer = 8                    
	Quiesce = 9                  
	Reboot = 10                  
	Reset = 11                   
	Saving = 32773               
	Pausing = 32776              
	Resuming = 32777             
	FastSaved = 32779            
	FastSaving = 32780           
	RunningCritical = 32781      
	OffCritical = 32782          
	StoppingCritical = 32783     
	SavedCritical = 32784        
	PausedCritical = 32785       
	StartingCritical = 32786     
	ResetCritical = 32787        
	SavingCritical = 32788       
	PausingCritical = 32789      
	ResumingCritical = 32790     
	FastSavedCritical = 32791    
	FastSavingCritical = 32792





class RequestedStateRes(Enum):
	Completed_with_No_Error = 0
	Access_Denied = 32769
	Transition_Started = 4096  #The transition is asynchronous.
	Invalid_State= 32775  # Invalid state for this operation


class JobState(Enum):
	New = 2  # The job has never been started.
	Starting = 3  # The job is moving from the 2 (New), 5 (Suspended), or 11 (Service) states into the 4 (Running) state.
	Running = 4  # The job is running.
	Suspended  = 5  # The job is stopped, but it can be restarted in a seamless manner.
	Shutting_Down = 6  # The job is moving to a 7 (Completed), 8 (Terminated), or 9 (Killed) state. 
	Completed = 7  # The job has completed normally.
	Terminated = 8  # The job has been stopped by a "Terminate" state change request. The job and all its underlying processes are ended and can be restarted only as a new job. The requirement that the job be restarted only as a new job is job-specific.
	Killed = 9 	# The job has been stopped by a "Kill" state change request. Underlying processes may still be running, and a clean-up might be required to free up resources.
	Job_Exception = 10  # The job is in an abnormal state that might be indicative of an error condition. The actual status of the job might be available through job-specific objects.
	Service = 11  # The job is in a vendor-specific state that supports problem discovery, or resolution, or both.

	@classmethod
	def list_of_values(cls, list_of_attr):
		return [cls.__getattr__(att).value for att in list_of_attr]


class MemoryChangeRc(Enum):
	Completed = 0 #Completed with No Error 
	Not_Supported = 1 
	Failed = 2
	Timeout = 3
	Invalid_Parameter = 4
	Invalid_State = 5
	Incompatible = 6
	Job_Started = 4096


class HeartBeatStatus(Enum):
	OK = 2  # The service is operating normally
	Degraded = 3  # The service is operating normally, but the guest service negotiated a compatible communications protocol version
	Non_RecoverableError = 7  # the guest does not support a compatible protocol version
	No_Contact = 12  # The guest service is not installed or has not yet been contacted
	Lost_Communication = 13  # The guest service is no longer responding normally
	Paused = 15  #  The virtual machine is paused


SERVICE_COMPONENTS =  { 
	"ShutDown": "Msvm_ShutdownComponentSettingData",
	"TimeSync": "Msvm_TimeSyncComponentSettingData", 
	"DataExchange": "Msvm_KvpExchangeComponentSettingData",
	"Backup": "Msvm_VssComponentSettingData",  # Shadow Copy Service
	"GuestServices": "Msvm_GuestServiceInterfaceComponentSettingData",
	"Hearybeat": "Msvm_HeartbeatComponentSettingData",
}


def connect_to_wmi(server: str, namespace: str) -> wmi.WMI:
	try:
		conn = wmi.connect_server(server, namespace=namespace)
	except pywintypes.com_error:
		#log connect to wmi failed
		raise infra_exceptions.ConnectToWmiError
	return wmi.WMI(wmi=conn)


def change_vm_state(client: wmi.WMI, vm_name: str, state: VmState) ->  wmi._wmi_object:
	vm = __get_vm_object(client, vm_name)
	job_res, rc = vm.RequestStateChange(state.value)
	if rc == RequestedStateRes.Transition_Started.value: #asyn start
		#check_if_job_succced
		if __handle_job_response(client, job_res):
			return vm
	else:
		raise infra_exceptions.ChangeVmStateError(f"RequestStateChange for vm {vm_name} returned with code {rc}")


def get_vms(client: wmi.WMI,  vm_name=None) -> list:
	vms_data = list()
	if vm_name == None:
		machines = client.Msvm_SummaryInformation()
		for machine in machines:
			vms_data.append(__create_vm_data(machine))
	else:
		machine = client.Msvm_SummaryInformation(ElementName=vm_name)
		if not machine:
			raise infra_exceptions.VmNotFoundError
		vms_data.append(__create_vm_data(machine))
	return vms_data


def __create_vm_data(machine: wmi._wmi_object):
	machine_data = {
		"name": machine.ElementName,
		"state": VmState(machine.EnabledState).name,
		"cpu_assigned": machine.NumberOfProcessors,
		"memory_usage": machine.MemoryUsage,
		"up_time": datetime.timedelta(milliseconds= int(machine.UpTime)),
		"wmi_object": machine}
	return machine_data



def set_vm_memory(client: wmi.WMI,  vm_name: str, ram: int, dynamic=None) -> bool: 
	# Ram in MB, v';.m memory can change only if the machine is off
	vm_mem_setting = __get_setting_data(client, vm_name, "Msvm_MemorySettingData")
	if ram % 2 != 0:
		raise infra_exceptions.ModifyVmError("Ram can be only even number")
	vm_mem_setting.VirtualQuantity = str(ram)
	if dynamic != None:
		vm_mem_setting.DynamicMemoryEnabled = dynamic

	mgmsv = client.Msvm_VirtualSystemManagementService()[0]
	job, res_resource_setting, rc = mgmsv.ModifyResourceSettings(ResourceSettings=[vm_mem_setting.GetText_(1)])
	if rc == MemoryChangeRc.Completed.value:
		return True
	elif rc == MemoryChangeRc.Job_Started.value:
		return __handle_job_response(client, job)  # use only for raise the error-exception from windows(if job failed but return with Completed rc it's can be bug)  
	else:
		raise infra_exceptions.ModifyVmError(f"change memory return with rc {rc} name = {MemoryChangeRc(rc).name}")


def set_vm_service(client: wmi.WMI, vm_name: str,service_name: str, enable:bool) -> bool:
	service = SERVICE_COMPONENTS.get(service_name)
	if service is None:
		raise infra_exceptions.ServiceNotExist(f"service - {service_name} is not exist")
	vm_service_setting = __get_setting_data(client, vm_name, service)
	vm_service_setting.EnabledState = "2" if enable else "3"
	mgmsv = client.Msvm_VirtualSystemManagementService()[0]
	jop, res, rc = mgmsv.ModifyGuestServiceSettings([vm_service_setting.GetText_(1)])
	if rc != 0:
		raise ModifyVmError(f"Modify service {service_name} failed with RC {rc}")
	return True


def get_services_status(client: wmi.WMI, vm_name: str) -> dict:
	services_status = dict()
	for service_name in SERVICE_COMPONENTS:
		status = get_service_status(client, vm_name, service_name)
		services_status[service_name] = status
	return services_status
   

def get_service_status(client:  wmi.WMI, vm_name: str, service_name: str) -> bool:
	service = SERVICE_COMPONENTS.get(service_name)
	if service is None:
		raise infra_exceptions.ServiceNotExist(f"service - {service_name} is not exist")
	vm_service_setting = __get_setting_data(client, vm_name, service)
	return True if vm_service_setting.EnabledState is 2 else False


def set_all_services_on(client: wmi.WMI, vm_name: str):
	for service_name in SERVICE_COMPONENTS:
		set_vm_service(client, vm_name, service_name, True)


def wait_for_heart_beat(client: wmi.WMI, vm_name: str, seconds=90) -> bool:
	logger.debug(f"[{vm_name}] wait for heart_beat")
	vm_id = __get_vm_id(client, vm_name)
	interval = 2
	start_time = time.time()
	elapsed_time = time.time() - start_time
	while elapsed_time < seconds:
		time.sleep(interval)
		elapsed_time = time.time() - start_time

		try:
			status = __get_heart_beat(client, vm_id)  # type - HeartBeatStatus
		except infra_exceptions.HeartBeatError:
			logger.warning(f"[{vm_name}] didn't turned on")
			return False
		if status == HeartBeatStatus.OK:
			logger.debug(f"[{vm_name}] heart beat returned:'ok'")
			return True
		elif status == HeartBeatStatus.No_Contact:
			logger.debug(f"[{vm_name}] still wait for heart beat {elapsed_time} seconds")
			interval += 1
		else:
			#Todo support pause and lost communication
			raise NotImplementedError("heart beat not support pause and lost communication yet")
	return False


def __get_heart_beat(client: wmi.WMI, vm_id: str) -> HeartBeatStatus:
	heart_beat = client.Msvm_HeartbeatComponent(SystemName=vm_id)  # return tuple with int inside
	if not heart_beat:
		raise infra_exceptions.HeartBeatError(f"Heart beat for {vm_id} not found")
	return HeartBeatStatus(heart_beat[0].OperationalStatus[0])


def __handle_job_response(client: wmi.WMI, job_res: str) -> bool:
	instance_id = __parse_instance_id(job_res)
	job = client.Msvm_ConcreteJob(InstanceID=instance_id)[0]
	if not job:
		raise infra_exceptions.JobNotFoundError(instance_id)
	if int(job.JobState) in JobState.list_of_values(["New", "Starting", "Running", "Suspended"]):
		time.sleep(0.5)
		#log the status
		return __handle_job_response(client, job_res)

	elif job.JobState in JobState.list_of_values(["Suspended", "Shutting_Down", "Terminated", "Killed"]):
		raise infra_exceptions.JobFailedError

	elif job.JobState == JobState.Job_Exception.value:
		raise infra_exceptions.JobFailedError(job.ErrorDescription)

	elif job.JobState == JobState.Completed.value:
		return True

	raise NotImplementedError(f"JobState returned with rc - {job.JobState} {JobState(job.JobState).name}")  #support in future if relevant


def __parse_instance_id(job_res: str) -> str:
    #instance_id len is 36 chars.
    size = len(job_res)
    instance_id = job_res[size - 37:size - 1]
    if len(instance_id) != 36:
        raise infra_exceptions.ParseinstanceIdError
    return instance_id


def __get_vm_object(client: wmi.WMI, vm_name: str) -> wmi._wmi_object:
	try:
		vm_obj = client.Msvm_ComputerSystem(ElementName=vm_name)
		if not vm_obj:
			#log Msvm_ComputerSystem return empty list
			raise infra_exceptions.VmNotFoundError(f"Vm {vm_name} not found")
		return vm_obj[0]
	except AttributeError:
		#log connect to wmi failed
		raise infra_exceptions.WmiQueryError("Msvm_ComputerSystem query failed")


def __get_vm_id(client: wmi.WMI, vm_name: str):
	return __get_vm_object(client, vm_name).Name


def __get_setting_data(client: wmi.WMI, vm_name: str, setting_data_type):
	vm_id = __get_vm_id(client, vm_name)
	for memory_data_setting in client.__getattr__(setting_data_type)():
		if vm_id in memory_data_setting.InstanceID:
			return memory_data_setting
	raise infra_exceptions.VmNotFoundError
	




		

if __name__ == "__main__":
	client = connect_to_wmi(HOST_NAME, r"root\virtualization\v2")
	set_vm_memory(client, "202H", 5000)
