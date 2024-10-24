#!/bin/bash
mkdir -p ./output/ping_output
python3 ../../pns-elecnet/cmd_scraper/command_scraper.py -c ./output/ping_commands.yaml -i 1 -o ./output/ping_output -d
