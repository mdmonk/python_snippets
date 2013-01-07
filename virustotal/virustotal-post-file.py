import postfile
host = "www.virustotal.com"
selector = "https://www.virustotal.com/api/scan_file.json"
fields = [("key", "1fe0ef5feca2f84eb450bc3617f839e317b2a686af4d651a9bada77a522201b0")]
file_to_send = open("test.txt", "rb").read()
files = [("file", "test.txt", file_to_send)]
json = postfile.post_multipart(host, selector, fields, files)
print json
# {"scan_id": "cd1384c10baa2d5b96f397b986e2a1fc9535d2ef0e185a113fc610eca1c6fb0e-1271623480", "result": 1}