import ipaddress
import dns.resolver  # NECESSARY TO INSTALL IT
import re


def get_all_ip_ranges(domain):
    dig_data = {}
    for to_parse in dns.resolver.query(domain, 'TXT'):
        parsed = str(to_parse).replace("\"", "").split('=', 1)
        dig_data[parsed[0]] = parsed[1]
    ip_ranges = re.findall("ip[4|6]:([^ ]+)", dig_data['v'])
    includes = re.findall("include:([^ ]+)", dig_data['v'])
    redirect = re.findall("redirect=([^ ]+)", dig_data['v'])
    if redirect:
        ip_ranges.extend(get_all_ip_ranges(redirect[0]))
    if includes:
        for include in includes:
            ip_ranges.extend(get_all_ip_ranges(include))
    return ip_ranges


def ip_belongs_to_domain(ip, domain):
    domain_ip_ranges = get_all_ip_ranges(domain)
    for ip_range in domain_ip_ranges:
        if ipaddress.ip_address(ip) in ipaddress.ip_network(ip_range):
            return True
    return False


print("\n".join(get_all_ip_ranges('uvigo.gal')))
print(ip_belongs_to_domain('2a01:4180:4051:0400::', 'usc.es'))

