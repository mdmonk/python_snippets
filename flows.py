#!/usr/bin/env python
from scapy.all import *
import os,sys,hashlib

class flows:
	def __init__(self, pcap):
		self.flows = {}
		self.pcap = pcap

		if not self.pcap or not os.path.exists(self.pcap):
			print "Must enter valid pcap file"
			return 0
	
	def main(self):
		#Read in the pcap
		pcap = rdpcap(self.pcap)

		#Process each packet in the pcap
		for p in pcap:
			self.handle_packet(p)

		#Return the stream objects
		return self.flows

	def handle_packet(self, p):
		if not IP in p or not TCP in p:
			#No IP layer or TCP layer
			return 0

		ip_src = p[IP].src
		ip_dst = p[IP].dst

		tcp_sport = p[TCP].sport
		tcp_dport = p[TCP].dport
		tcp_flags = p[TCP].flags

		#Get a unique identifier for the TCP Flow
		flow_hash  = hashlib.md5(str(ip_src) + str(ip_dst) + str(tcp_sport) + str(tcp_dport)).hexdigest()

		#If it is an unknown flow create a new flow object
		if not flow_hash in self.flows:
			s = flow_obj()
			self.flows[flow_hash] = s

			#Set IP and TCP information
			s.src = ip_src
			s.dst = ip_dst
			s.sport = tcp_sport
			s.dport = tcp_dport

			#If the initial packet is a SYN it is to the server
			if tcp_flags == 2:
				s.direction = "to-server"
			#Else if it is a SYN-ACK it is to the client
			elif tcp_flags == 18:
				s.direction = "to-client"
	
		#If the flow is already known
		elif flow_hash in self.flows:
			s = self.flows[flow_hash]

		#Append the current packet
		s.packets.append(p)
		
		#Get the raw data from the packet
		raw_layer = p.getlayer(Raw)
		if raw_layer:
			s.raw += raw_layer.load


class flow_obj:
	def __init__(self, direction="", packets=[], raw="", src="", dst="", sport="", dport=""):
		self.direction = direction
		self.packets = packets
		self.raw = raw
		self.src = src
		self.dst = dst
		self.sport = sport
		self.dport = dport
