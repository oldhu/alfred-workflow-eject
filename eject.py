import subprocess
import plistlib
import json
import sys

ITEMS = []

def execute(cmd):
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	p.wait()
	lines = p.stdout.readlines()
	return lines

def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Y', suffix)

def is_ejectable(devId):
	lines = execute('diskutil info -plist ' + devId)
	root = plistlib.readPlistFromString("".join(lines))
	return root['Ejectable']

def loadItem(item):
	global ITEMS
	devId = item['DeviceIdentifier']

	if not is_ejectable(devId):
		return

	volumeName = ''
	if 'VolumeName' in item:
		volumeName = item['VolumeName'] 
	size = 0
	if 'Size' in item:
		size = int(item['Size'])
	mountPoint = ''
	if 'MountPoint' in item:
		mountPoint = item['MountPoint']

	ITEMS.append({
		"title": volumeName, 
		"subtitle": mountPoint + " " + sizeof_fmt(size),
		"arg": devId
	})

def query():
	global ITEMS
	lines = execute('diskutil list -plist')
	root = plistlib.readPlistFromString("".join(lines))
	for disk in root['WholeDisks']:
		for item in root['AllDisksAndPartitions']:
			if item['DeviceIdentifier'] == disk:
				if 'Partitions' in item:
					for part in item['Partitions']:
						loadItem(part)
				else:
					loadItem(item)

	if len(ITEMS) > 0:
		ITEMS = [{
			"title": "all",
			"subtitle": "eject all disks",
			"arg": "all"
		}] + ITEMS
	else:
		ITEMS = [{
			"title": "0 ejectable disk",
			"subtitle": "no disk to eject",
			"arg": "none"
		}]

	allitems = []
	for item in ITEMS:
		item["icon"] = {
			"path": "hard_disk.png"
		}
		allitems.append(item)
	print json.dumps({"items" : allitems})	


def eject_disk(disk):
	execute("diskutil umount force " + disk)
	execute("diskutil eject " + disk)
	notification_cmd = 'osascript -e \'display notification "' + disk + '" with title "Eject Disk Success"\''
	execute(notification_cmd)

def eject_disk_all():
	global ITEMS
	lines = execute('diskutil list -plist')
	root = plistlib.readPlistFromString("".join(lines))
	for disk in root['WholeDisks']:
		for item in root['AllDisksAndPartitions']:
			if item['DeviceIdentifier'] == disk:
				if 'Partitions' in item:
					for part in item['Partitions']:
						loadItem(part)
				else:
					loadItem(item)

	if len(ITEMS) > 0:
		for item in ITEMS:
			eject_disk(item['arg'])	

def eject(disk):
	if disk == 'all':
		eject_disk_all()
	elif disk == 'none':
		pass
	else:
		eject_disk(disk)

if __name__ == '__main__':	
	if (sys.argv[1] == 'query'):
		query()
	if (sys.argv[1] == 'eject'):
		eject(sys.argv[2])