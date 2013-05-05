#!/usr/bin/env python

'''
Display the AWS instances by tags
'''

# Python libs
import ConfigParser
import cgi
import os

# Third party libs
import boto.ec2
from jinja2 import Environment, FileSystemLoader

# Functions
def get_instances(awskey, awssec):
	'''
	get all the instances from Amazon with the specific keys
	'''
	
	ret = []
	for region in boto.ec2.regions():
		conn = boto.ec2.connect_to_region(region.name, aws_access_key_id=awskey, aws_secret_access_key=awssec)
		reservations = conn.get_all_instances()
		ret += [i for r in reservations for i in r.instances]
		conn.close()
	
	return ret

def get_all_envs(instances):
	ret = []
	for instance in instances:
		try:
			ret.append(instance.__dict__['tags']['env'])
		except KeyError:
			pass
	return list(set(ret))

def get_interesting_data(instances):
	
	# Init hash
	ret = {}
	for env in get_all_envs(instances):
		ret[env] = {}
	ret['unknown'] = {}
	
	# put each instance in its place
	for instance in instances:
		try:
			env = instance.__dict__['tags']['env']
		except KeyError:
			env = 'unknown'
		try:
			role = instance.__dict__['tags']['role']
		except KeyError:
			role = 'unknown'
		
		ret[env][instance.__dict__['id']] = {
			'role': role,
			'type': instance.__dict__['root_device_type'],
			'state': instance.__dict__['_state'],
			'keypair': instance.__dict__['key_name'],
			'private_ip': instance.__dict__['private_ip_address'],
			'public_ip': instance.__dict__['ip_address'],
			'zone': instance.__dict__['_placement'],
			'launch_time': instance.__dict__['launch_time'],
			'size': instance.__dict__['instance_type']
		}
	
	return ret

def print_env(env, data):
	'''
	print a table of the environment
	'''
	
	THIS_DIR = os.path.dirname(os.path.abspath(__file__))
	j2_env = Environment(loader=FileSystemLoader(THIS_DIR), trim_blocks=True)
	ret = ''
	ret += '<p align="center"><h1>{0} instances</h1></p>'.format(env)
	ret += '<p align="center">{0}</p>'.format( j2_env.get_template('env.html').render(env=env, hosts=data[env]) )
	
	return ret

def get_getconfig():
	config = ConfigParser.ConfigParser()
	base = os.path.dirname(__file__)
	if not base:
		base = '.'
	config.read( '{0}/keys.cfg'.format(base) )
	return config

def print_keys(keys, config):
	
	if keys == False:
		return ''
	
	ret = ''
	instances = get_instances( config.get(keys, 'key'), config.get(keys, 'secret') )
	data = get_interesting_data(instances)
	for env in data:
		if env != 'unknown':
			ret += print_env(env, data)
	ret += print_env('unknown', data)
	
	return ret

def print_sections(config):
	
	ret = '<br>'
	for sec in config.sections():
		ret += '<a href="/?key={0}">{0}</a><br>'.format(sec)
	return ret
	


HEADER = """
<html>
<head>
<title>AWS View</title>
<style type="text/css">
<!--
@import url("style.css");
-->
</style>
</head>
<body align="center">
"""

FOOTER = """
</body>
</html>
"""

# Main
try:
	keys = cgi.FieldStorage()['key'].value
except KeyError:
	keys = False
config = get_getconfig()

# HTML
print "Content-type: text/html"
print
print HEADER
print """
<table width="100%" text-align="center">
	<tr>
		<td align="center" colspan=2 >
			<h1>AWS View</h1>
		</td>
	</tr>
	
	<tr>
		<td width="10%" align="center" valign="top">
			{0}
		</td>
		
		<td width="90%" align="center">
			{1}
		</td>
	</tr>
</table>
""".format( print_sections(config), print_keys(keys, config) )
print FOOTER

