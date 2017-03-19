#!/usr/bin/python

from sys import argv
import argparse
import paramiko
import re

parser = argparse.ArgumentParser(description="pyfimon - Python File Monitor tool")
parser.add_argument('host', help="List of hostnames")
parser.add_argument('file', help="File to change")
parser.add_argument('scmd', help="Sed command")
parser.add_argument('--ssh_user', help="SSH Username")
parser.add_argument('--ssh_pass', help="SSH Password")

args = parser.parse_args()

ssh_command = (
               "if [ -e " + args.file + " ]; then\n"+ 
               "\tsed -i.bak \"" + re.sub(r"([\"'|&;])", r"\\\1", args.scmd) + "\" " + args.file + "\n" +
               "\tDIFF=$(diff -q " + args.file + " " + args.file + ".bak)\n" +                    
               "\tif [ \"$DIFF\" ]; then\n"+
               "\t\tDIFF=$(diff -y -W120 " + args.file + " " + args.file + ".bak)\n"+
               "\t\techo \"$DIFF\"\n"+
               "\tfi\n"+
               "fi"
              )

#print(ssh_command)

with open("/etc/hosts") as hostfile:
    for line in hostfile:

        if '#' in line[0]:
            continue

        host_regex = r"^(.*)\s+"+re.escape(args.host)+r"$"
        host_match = re.match(host_regex, line)

        if host_match:
            ip = host_match.group(1).strip(' ')
            break

if ip:
    print("Attempting to connect to ", ip)
    ssh_client = paramiko.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip, username=args.ssh_user, password=args.ssh_pass)

    stdin, stdout, stderr = ssh_client.exec_command(ssh_command)
    for outline in stdout.readlines():
        print(outline, end="")
