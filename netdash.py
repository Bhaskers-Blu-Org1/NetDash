#!/usr/bin/env python3
"""Program Start"""

import argparse
import ipaddress
import logging
import shlex
import sys
import threading

import src.pinger as pinger
import src.ui as ui
import src.config as config
from src.host import Host, hosts


DEFAULT_TIME = 30     # Default update cycle time
DEFAULT_PING_NUM = 1  # Default number of pings to send

TIME_HELP = "update cycle time (in seconds)"                # Time argument help message
COUNT_HELP = "number of pings to send per host each cycle"  # Count argument help message
QUIET_HELP = "supress informational messages"               # Quiet argument help message


def positive_int(in_value):
    """Check if argument is a positive integer"""

    try:
        value = int(in_value)
    except ValueError:
        raise argparse.ArgumentTypeError(in_value + " is not a valid positive integer")

    if value <= 0:
        raise argparse.ArgumentTypeError(in_value + " is not a valid positive integer")

    return value


# Format log, remove username and insert a space
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')

# Parse command line arguments
parser = argparse.ArgumentParser(description="Network monitoring dashboard")
parser.add_argument('path', help="path to configuration file")
parser.add_argument('-t', '-time', nargs=1, type=positive_int, default=[DEFAULT_TIME], metavar='#', help=TIME_HELP)
parser.add_argument('-c', '-count', nargs=1, type=positive_int, default=[DEFAULT_PING_NUM], metavar='#',
                    help=COUNT_HELP)
parser.add_argument('-q', '-quiet', action='store_true', default=False, help=QUIET_HELP)

args = parser.parse_args()
config.cycle_time = args.t[0]
config.ping_number = args.c[0]

# Set quiet option
config.set_quiet(args.q)

# Open configuration file at specified path
try:
    file = open(args.path)
except FileNotFoundError:
    logging.critical("File does not exist.")
    sys.exit(2)
except IsADirectoryError:
    logging.critical("Path is to a directory.")
    sys.exit(2)

# Parse configuration file
for line_num, line in enumerate(file.readlines()):
    line = line.strip()

    # Skip blank lines and comments
    if not line or line[0] == '#':
        continue
    line_parts = shlex.split(line)

    # Check validity of ip address, otherwise, skip it
    try:
        addr = ipaddress.ip_address(line_parts[0])
    except ValueError:
        logging.error("IP address on line " + str(line_num + 1) + " is not valid, skipping it.")
        continue

    # Subsequent additions of optional fields will require a "None" value to be supported
    # If a label exists, use it
    label = None
    if len(line_parts) > 1:
        label = line_parts[1]

    # Add the host to the list
    hosts.append(Host(addr, label=label))

file.close()

# Start pinger thread
threading.Thread(target=pinger.ping_all, name="Pinger", daemon=True).start()

# Start GUI
ui.start_gui()
