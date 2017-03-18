#!/usr/bin/python

from sys import argv

args = argv

hosts = []

for hostname in argv[1:]:
    with open("/etc/hosts") as hostfile:
        for line in hostfile:

            if '#' in line[0]:
                continue

            if hostname in line:
                hosts.append(line.split(' ')[0])

for ip in hosts:
    print(ip)
