from bootstrapvz.common import task_groups
import tasks.packages
import tasks.boot
import tasks.image
from bootstrapvz.common.tasks import loopback
from bootstrapvz.common.tasks import initd
from bootstrapvz.common.tasks import ssh


def initialize():
	pass


def validate_manifest(data, validator, error):
	import os.path
	schema_path = os.path.normpath(os.path.join(os.path.dirname(__file__), 'manifest-schema.json'))
	validator(data, schema_path)


def resolve_tasks(taskset, manifest):
	taskset.update(task_groups.get_standard_groups(manifest))

	taskset.update([tasks.packages.DefaultPackages,
	                loopback.Create,
	                initd.InstallInitScripts,
	                ssh.AddOpenSSHPackage,
	                ssh.ShredHostkeys,
	                ssh.AddSSHKeyGeneration,
	                tasks.packages.Waagent,
	                tasks.boot.ConfigureGrub,
	                tasks.image.ConvertToVhd,
	                ])


def resolve_rollback_tasks(taskset, manifest, completed, counter_task):
	taskset.update(task_groups.get_standard_rollback_tasks(completed))
