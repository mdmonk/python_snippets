import simplejson
import urllib
import urllib2
url = "https://www.virustotal.com/api/get_file_report.json"
parameters = {"resource": "99017f6eebbac24f351415dd410d522d", "key": "1fe0ef5feca2f84eb450bc3617f839e317b2a686af4d651a9bada77a522201b0"}
data = urllib.urlencode(parameters)
req = urllib2.Request(url, data)
response = urllib2.urlopen(req)
json = response.read()
print json


{"report": ["2010-04-13 23:28:27", {"nProtect": "", 
                                    "CAT-QuickHeal": "", 
                                    "McAfee": "Generic.dx!rkx", 
                                    "TheHacker": "Trojan/VB.gen", 
                                    "VirusBuster": "", 
                                    "NOD32": "a variant of Win32/Qhost.NTY", 
                                    "F-Prot": "", "Symantec": "", 
                                    "Norman": "", 
                                    "a-squared": "Trojan.Win32.VB!IK", ...}], 
 "permalink": "http://www.virustotal.com/file-scan/report.html?id=a8...",
 "result": 1}
>>> response_dict = simplejson.loads(json)
>>> response_dict.get("report")
['2010-04-13 23:28:27', {'nProtect': '', 'CAT-QuickHeal': '', 
'McAfee': 'Generic.dx!rkx', 'TheHacker': 'Trojan/VB.gen', 
'VirusBuster': '', 'NOD32': 'a variant of Win32/Qhost.NTY', 
'F-Prot': '', 'Symantec': '', 'Norman': '', 'Avast': 'Win32:Malware-gen', 
'eSafe': 'Win32.TRVB.Acgy', 'ClamAV': '', 'Kaspersky': 'Trojan.Win32.VB.acgy', 
'BitDefender': 'Trojan.Generic.3611249', 'Comodo': 'Heur.Suspicious', 
'F-Secure': 'Trojan.Generic.3611249', 'DrWeb': 'Trojan.Hosts.37', 
'AntiVir': 'TR/VB.acgy.1', 'TrendMicro': '', 'McAfee-GW-Edition': 'Trojan.VB.acgy.1', 
'Sophos': '', 'eTrust-Vet': '', 'Authentium': '', 'Jiangmin': '', 
'Antiy-AVL': 'Trojan/Win32.VB', 'a-squared': 'Trojan.Win32.VB!IK', 
'Microsoft': '', 'ViRobot': '', 'Prevx': 'Medium Risk Malware', 
'GData': 'Trojan.Generic.3611249', 'AhnLab-V3': '', 'VBA32': '', 
'Sunbelt': 'Trojan.Win32.Generic!BT', 'PCTools': '', 'Rising': '', 
'Ikarus': 'Trojan.Win32.VB', 'Fortinet': '', 'AVG': 'Generic17.ASTJ', 
'Panda': 'Adware/AccesMembre', 'Avast5': 'Win32:Malware-gen'}]