# Assumes CORE network has been scrapped by cmd scraper
# Re-jigs files into cumulums concattenated format, + iptables overlays.

import re
import os
from pathlib import Path
import json
import ipaddress

INPUT_DIR = Path("/Users/adamhamilton/Postdoc/CodingProjects/elecnet_batfish-1/elecnet_config/output/config_output")
OUTPUT_DIR = Path("networks/elecnet/")

# Parse commands and responses

cmds = {}
hostname, command, response = "", "", ""

for filename in INPUT_DIR.glob("*.txt"):
    for line in open(filename, "r").readlines():
        match = re.match(r"^(?:.*@)?([\w\d\-\.]+)#\s*(.*)", line)
       
        if match:
            if response != "":
                cmds.setdefault(hostname, {})
                cmds[hostname][command] = response
            hostname, command = match.groups()
            response = ""
        else:
            response += line


def ip_addr_json_to_etc_interfaces(json) -> str:
    output = ""
    for i in json:
        output += f"auto {i['ifname']}\n"
        output += f"iface {i['ifname']} inet static\n"
        for addr in i["addr_info"]:
            # TODO: IPv6
            if addr["family"] == "inet":
                # ip = ipaddress.ip_interface((addr["local"],addr["prefixlen"]))
                # output += f"        address {ip.ip}\n"
                # output += f"        netmask {ip.netmask}\n"
                output += (
                    f"        address {addr['local']+'/'+str(addr['prefixlen'])}\n"
                )
        output += "\n"
    return output


def ip_addr_json_to_host_json(json) -> dict:
    out = {}
    for i in json:
        ifname = i["ifname"]

        # Skip the loopback interface for hosts
        if ifname == "lo":
            continue

        out[ifname] = {}
        out[ifname]["name"] = ifname

        for addr in i["addr_info"]:
            # TODO: IPv6
            if addr["family"] == "inet":
                out[ifname]["prefix"] = addr["local"] + "/" + str(addr["prefixlen"])

    return out


def defaultroute_sh_gateway(cmd: str) -> str:
    match = re.search(r"ip route add default via (.*)\n", cmd)
    if match:
        return match.groups()[0]


# Create batfish format
(OUTPUT_DIR / "configs").mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "hosts").mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "iptables").mkdir(parents=True, exist_ok=True)

for hostname in cmds:
    addr = json.loads(cmds[hostname]["ip --json addr"])
    router = False
    # Router config in the cumulus-linux format https://batfish.readthedocs.io/en/latest/formats.html#cumulus-linux
    if "show run" in cmds[hostname]:
        router = True
        config = f"{hostname}\n"

        config += "# This file describes the network interfaces\n"
        config += ip_addr_json_to_etc_interfaces(addr)

        config += "# ports.conf --\n\n"
        # No ports.conf information

        config += "frr version\n"
        config += cmds[hostname]["show run"]

        with open(OUTPUT_DIR / "configs" / (hostname + ".cfg"), "w") as f:
            f.write(config)

    # IPTables
    iptables = False
    if "iptables -S" in cmds[hostname]:
        iptables = True
        with open(OUTPUT_DIR / "iptables" / (hostname + ".iptables"), "w") as f:
            f.write(cmds[hostname]["iptables -S"])

    # Host File https://batfish.readthedocs.io/en/latest/formats.html#modeling-hosts
    host = {"hostname": hostname}

    if addr:
        host["hostInterfaces"] = ip_addr_json_to_host_json(addr)

        # If there is a default gateway, apply it to the 1st interface
        if "cat defaultroute.sh" in cmds[hostname]:
            next(iter(host["hostInterfaces"].values()))["gateway"] = defaultroute_sh_gateway(
                cmds[hostname]["cat defaultroute.sh"]
            )

    if router:
        host["overlay"] = True

    if iptables:
        # Always / path even on Windows
        host["iptablesFile"] = "iptables/" + (hostname + ".iptables")

    with open(OUTPUT_DIR / "hosts" / (hostname + ".json"), "w") as f:
        json.dump(host, f, indent=4)


# format:
# (hostname)
# # This file describes the network interfaces
# (interfaces in /etc/interfaces format)
# # ports.conf --
# frr version
# (the show run)

# then fill out the hosts.json file
