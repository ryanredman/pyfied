#!/usr/bin/python

# pyfied - Python File Editor
# Written by Ryan Redman

# Script resolves a given hostname via /etc/hosts,
# and then issues a sed command on a given file on
# that host.
#
# Script returns the diff patch for the changed file,
# and creates a backup file on the remote host.

import argparse
import getpass
import paramiko
import re
import sys

parser = argparse.ArgumentParser(description="%(prog)s - Python File Editor",
                                 usage="%(prog)s [--help | -h] [--ssh_user USERNAME] [--ssh_pass PASSWORD] host file cmd [cmd ...]")

### Required ###
parser.add_argument('host', help="Hostname")
parser.add_argument('file', help="File to change")
parser.add_argument('cmd', nargs="*",  help="Sed command")

### Optional ###
parser.add_argument('--ssh_user', help="SSH Username")
parser.add_argument('--ssh_pass', help="SSH Password")

args = parser.parse_args()

if not args.ssh_user:
    args.ssh_user = input("SSH username: ")

if not args.ssh_pass:
    args.ssh_pass = getpass.getpass("SSH password: ")

with open("/etc/hosts") as hostfile:
    for line in hostfile:

        if '#' in line[0]:
            continue

        if args.host in line:
            ip = line.split()[0]
            break

try:
    ip
except NameError:
    print("Unable to locate ip address for hostname: " + args.host, file=sys.stderr)
    sys.exit(1)
else:
    
    # Bash script we send over SSH -
    #     1. Checks if file exists
    #     2. If it does, it takes the commands passed in as an argument to this script,
    #        escapes any potentially dubious charcters, and creates a sed command in the
    #        form: sed -i.bak -e *cmd* -e *cmd2* -e *cmd3* *file*
    #     3. Then check to see if the backup file made by sed (-i.bak) differs from the
    #        current state of the file.
    #     4. If it does then we output the diff results to stdout so that they can be
    #        piped into a file to create a patch.

    sed_command = "sed -i.bak "
    for sc in args.cmd:
        sed_command += "-e \"" + re.sub(r"([\"'|&;$])", r"\\\1", sc) + "\" "
        
    ssh_command = (
                "if [ -e " + args.file + " ]; then\n"+ 
                "\t"+ sed_command + args.file + "\n" +
                "\tDIFF=$(diff -q " + args.file + ".bak " + args.file + ")\n" +                    
                "\tif [ \"$DIFF\" ]; then\n"+
                "\t\tDIFF=$(diff " + args.file + ".bak " + args.file + ")\n"+
                "\t\techo \"$DIFF\"\n"+
                "\telse\n"+
                "\t\techo \"No Changes Written.\"\n"+
                "\tfi\n"+
                "else\n"+
                "\t(echo >&2 \"Error: Unable to locate file: \"" + args.file + "; exit 1)\n"+
                "fi"
                )
    
    print("Attempting to connect to: " + args.host + " (" + ip + ")", file=sys.stderr)
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(ip, username=args.ssh_user, password=args.ssh_pass)
        print("Connected to: " + args.host + " (" + ip + ")", file=sys.stderr)
    except paramiko.AuthenticationException:
        print("Authentication failure to: " + args.host + " (" + ip + ")", file=sys.stderr)
        sys.exit(1)
    except:
        print("Unable to SSH to: " + args.host + " (" + ip + ")", file=sys.stderr)
        sys.exit(1)

    stdin, stdout, stderr = ssh_client.exec_command(ssh_command)
    exit_code = stdout.channel.recv_exit_status()

    if exit_code != 0:
        for errline in stderr.readlines():
            print(errline, end="", file=sys.stderr)
        print("Exit code: " + str(exit_code), file=sys.stderr)
        sys.exit(1)
    else:
        for outline in stdout.readlines():
            print(outline, end="")
        sys.exit(0)
