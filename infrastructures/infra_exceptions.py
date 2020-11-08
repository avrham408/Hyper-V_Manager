class VmNotFoundError(Exception):
	pass

class ChangeVmStateError(Exception):
	pass


class ParseInstanseIdError(Exception):
	pass


class JobFailedError(Exception):
	pass


class JobNotFoundError(Exception):
	pass


class ConnectToWmiError(Exception):
	pass


class WmiQueryError(Exception):
	pass


class ModifyVmError(Exception):
	pass


class ServiceNotExist(Exception):
	pass


class HeartBeatError(Exception):
	pass