from bootstrapvz.base import Task
from .. import phases
from ..tools import log_check_call
import filesystem
import kernel
from bootstrapvz.base.fs import partitionmaps
import os.path


class AddGrubPackage(Task):
	description = 'Adding grub package'
	phase = phases.preparation

	@classmethod
	def run(cls, info):
		info.packages.add('grub-pc')


class ConfigureGrub(Task):
	description = 'Configuring grub'
	phase = phases.system_modification
	predecessors = [filesystem.FStab]

	@classmethod
	def run(cls, info):
		from bootstrapvz.common.tools import sed_i
		grub_def = os.path.join(info.root, 'etc/default/grub')
		sed_i(grub_def, '^#GRUB_TERMINAL=console', 'GRUB_TERMINAL=console')
		sed_i(grub_def, '^GRUB_CMDLINE_LINUX_DEFAULT="quiet"',
		                'GRUB_CMDLINE_LINUX_DEFAULT="console=ttyS0"')


class InstallGrub_1_99(Task):
	description = 'Installing grub 1.99'
	phase = phases.system_modification
	predecessors = [filesystem.FStab]

	@classmethod
	def run(cls, info):
		p_map = info.volume.partition_map

		# GRUB screws up when installing in chrooted environments
		# so we fake a real harddisk with dmsetup.
		# Guide here: http://ebroder.net/2009/08/04/installing-grub-onto-a-disk-image/
		from ..fs import unmounted
		with unmounted(info.volume):
			info.volume.link_dm_node()
			if isinstance(p_map, partitionmaps.none.NoPartitions):
				p_map.root.device_path = info.volume.device_path
		try:
			[device_path] = log_check_call(['readlink', '-f', info.volume.device_path])
			device_map_path = os.path.join(info.root, 'boot/grub/device.map')
			partition_prefix = 'msdos'
			if isinstance(p_map, partitionmaps.gpt.GPTPartitionMap):
				partition_prefix = 'gpt'
			with open(device_map_path, 'w') as device_map:
				device_map.write('(hd0) {device_path}\n'.format(device_path=device_path))
				if not isinstance(p_map, partitionmaps.none.NoPartitions):
					for idx, partition in enumerate(info.volume.partition_map.partitions):
						device_map.write('(hd0,{prefix}{idx}) {device_path}\n'
						                 .format(device_path=partition.device_path,
						                         prefix=partition_prefix,
						                         idx=idx + 1))

			# Install grub
			log_check_call(['chroot', info.root, 'grub-install', device_path])
			log_check_call(['chroot', info.root, 'update-grub'])
		finally:
			with unmounted(info.volume):
				info.volume.unlink_dm_node()
				if isinstance(p_map, partitionmaps.none.NoPartitions):
					p_map.root.device_path = info.volume.device_path


class InstallGrub_2(Task):
	description = 'Installing grub 2'
	phase = phases.system_modification
	predecessors = [filesystem.FStab]
	# Make sure the kernel image is updated after we have installed the bootloader
	successors = [kernel.UpdateInitramfs]

	@classmethod
	def run(cls, info):
		log_check_call(['chroot', info.root, 'grub-install', info.volume.device_path])
		log_check_call(['chroot', info.root, 'update-grub'])
