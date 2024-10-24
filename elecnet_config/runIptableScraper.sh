#!/bin/bash
mkdir -p ./output/iptables_output
python3 ../../pns-elecnet/cmd_scraper/command_scraper.py -c ../../pns-elecnet/cmd_scraper/iptables_commands.yml -i 1 -o ./output/iptables_output -d
