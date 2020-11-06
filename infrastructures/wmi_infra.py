import wmi 
from enum import Enum
import pywintypes
from infrastructures import infra_exceptions
import time
import datetime


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


def connect_to_wmi(server: str, namespace: str) -> wmi.WMI:
	try:
		conn = wmi.connect_server(server, namespace=namespace)
	except pywintypes.com_error:
		#log connect to wmi failed
		raise infra_exceptions.ConnectToWmiError
	return wmi.WMI(wmi=conn)


def change_vm_state(client: wmi.WMI, vm_name: str, state: VmState) ->  wmi._wmi_object:
	try:
		computer_systems = client.Msvm_ComputerSystem()
		if not computer_systems:
			#log Msvm_ComputerSystem return empty list
			return False
	except AttributeError:
		#log connect to wmi failed
		return False
	vm = __get_specific_vm(computer_systems, vm_name)
	job_res, res_code = vm.RequestStateChange(state)
	if res_code == 4096: #asyn start
		#check_if_job_succced
		if __handle_job_response(client, job_res):
			return vm
	else:
		raise infra_exceptions.ChangeVmStateError(f"RequestStateChange for vm {vm_name} returned with code {res_code}")


def get_vms(client: wmi.WMI,  vm_name=None) -> list:
	vms_data = list()
	machines = client.Msvm_SummaryInformation()
	for machine in machines:
		machine_data = {
		"name": machine.ElementName,
		"state": VmState(machine.EnabledState).name,
		"cpu_usage": machine.NumberOfProcessors,
		"memory_usage": machine.MemoryUsage,
		"up_time": datetime.timedelta(milliseconds= int(machine.UpTime)),
		"wmi_object": machine}
		vms_data.append(machine_data)
	return vms_data


def __handle_job_response(client: wmi.WMI, job_res: str) -> bool:
	instanse_id = __parse_instance_id(job_res)
	job = client.Msvm_ConcreteJob(InstanceID=instanse_id)[0]
	if not job:
		raise infra_exceptions.JobNotFoundError(instanse_id)
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

	raise Exception("somthing crazy happend!!!")


def __parse_instance_id(job_res: str) -> str:
    #instanse_id len is 36 chars.
    size = len(job_res)
    instanse_id = job_res[size - 37:size - 1]
    if len(instanse_id) != 36:
        raise infra_exceptions.ParseInstanseIdError
    return instanse_id


def __get_specific_vm(list_of_wmi_objects, vm_name) -> wmi._wmi_object:
	for vm_obj in list_of_wmi_objects:
		if vm_obj.ElementName == vm_name:
			return vm_obj
	raise infra_exceptions.VmNotFoundError