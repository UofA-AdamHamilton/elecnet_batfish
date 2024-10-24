#!/bin/bash
mkdir -p ./output/iptables_output
python3 ../../pns-elecnet/cmd_scraper/command_scraper.py -c ../../pns-elecnet/cmd_scraper/config_commands.yml -i 1 -o ./output/config_output -d
