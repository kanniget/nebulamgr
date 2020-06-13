import yaml

import argparse

# Initiate the parser
parser = argparse.ArgumentParser()
parser.add_argument("-V", "--version", help="show program version", action="store_true")

# Read arguments from the command line
args = parser.parse_args()

# Check for --version or -V
if args.version:
    print("This is myprogram version 0.1")
    
print("Yay I Win!")