#!/usr/bin/python

from sys import argv
import argparse
import paramiko
import re

parser = argparse.ArgumentParser(description="pyfimon - Python File Monitor tool")
parser.add_argument('hosts', nargs='?', help="List of hostnames")
parser.add_argument('--ssh_user', help="SSH Username")
parser.add_argument('--ssh_pass', help="SSH Password")

args = parser.parse_args()

hosts = []

for hostname in args.hosts.split(" "):
    with open("/etc/hosts") as hostfile:
        for line in hostfile:

            if '#' in line[0]:
                continue

            host_regex = r"^(.*)\s+"+re.escape(hostname)+r"$"
            host_match = re.match(host_regex, line)

            if host_match:
                hosts.append(host_match.group(1).strip(' '))

for ip in hosts:
    print("Attempting to connect to ", ip)
    ssh_client = paramiko.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip, username=args.ssh_user, password=args.ssh_pass)
    stdin, stdout, stderr = ssh_client.exec_command("uptime")

    print(stdout.readlines())
