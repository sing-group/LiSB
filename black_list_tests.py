import ipaddress

ip: ipaddress.IPv4Address = ipaddress.ip_address('172.20.10.5')

print(ip.compressed)
print(ip.compressed in ['172.20.10.5'])
