#!/usr/bin/python3

import argparse
import os
import subprocess
from configparser import ConfigParser

from jinja2 import Environment, PackageLoader, select_autoescape

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class ConfigError(Error):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

def backup_file(filename):
    if os.path.exists(filename+".old"):
       try:    
          os.remove(filename+".old")
       except FileNotFoundError:
          print(" No backup file to remove")
    try:    
        os.rename(filename,filename+".old")
    except FileNotFoundError:
        print(" No original file to backup")

def resolveLighthouseAddress(lighthousename, config):
    for host_entry in config.get_config(section="hosts"):
        for name in host_entry:
            if lighthousename == name:
                return host_entry[name]["address"]
    raise ConfigError("Lighthouse name not found in host list")     

def build_host(hostname, config):
    # if hostname == "lighthouse":
    #     host = {"name": hostname, "groups": [], "outbound": [], "inbound": []}
    # else:
    for host_entry in config.get_config(section="hosts"):
        for name in host_entry:
            if hostname == name:
                host = host_entry[hostname]
                host["name"] = hostname
                host["outbound"] = []
                host["inbound"] = []
                host["groups"] = []
    for group in config.get_config(section="groups"):
        for groupname in group:
            for member in group[groupname]:
                if member == hostname:
                    host["groups"].append(groupname)
    security = config.get_config(section="security")
    for ruleclass in security:
        if ruleclass == "outbound":
            for rule in security[ruleclass]:
                host["outbound"].append(rule)
        else:
            for rule in security[ruleclass]:
                if rule["destination"] == "any":
                    host[ruleclass].append(rule)
                elif rule["destination"] == "all":
                    host[ruleclass].append(rule)
                elif rule["destination"] == hostname:
                    host[ruleclass].append(rule)
    return host


def sign_certs(hostname, config, regen):
    print("     " + hostname)
    for host_entry in config.get_config(section="hosts"):
        for name in host_entry:
            if hostname == name:
                host = host_entry[hostname]
    host_groups = []
    for group in config.get_config(section="groups"):
        for groupname in group:
            for member in group[groupname]:
                if member == hostname:
                    host_groups.append(groupname)
    ca_key = config.get_config("ca_cert")["key"]
    ca_crt = config.get_config("ca_cert")["crt"]
    args = []
    args.append(config.get_config(section="nebula-cert"))
    args.append("sign")
    args.append("-name")
    args.append(hostname)
    args.append("-ip")
    args.append(host["address"] + "/" + config.get_config(section="cidr"))
    args.append("-ca-crt")
    args.append(ca_crt)
    args.append("-ca-key")
    args.append(ca_key)
    groups = None
    if len(host_groups) > 0:
        args.append("-groups")
        for group in host_groups:
            if groups is None:
                groups = group
            else:
                groups = groups + "," + group
        args.append('"' + groups + '"')
    workdir = config.get_config("output") + "/" + hostname + "/"
    if regen:
        backup_file(workdir+hostname+".crt")
        backup_file(workdir+hostname+".key")

    try:        
        result = subprocess.run(args, cwd=workdir, capture_output=True)
    except TypeError:
        result = subprocess.run(args, cwd=workdir)
    if result.returncode > 0:
        if ( result.returncode == 1)  and regen:
            raise ConfigError("Cert gen failed with return code " + str(result.returncode))
        # print(" Cert gen failed with return code " + str(result.returncode))
        # print(result.stdout.decode("utf-8"))
        # print(result.stderr.decode("utf-8"))


def build_conf(hostname, config):
    env = Environment(
        loader=PackageLoader("nebulamgr", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    templatename = config.get_config(section="template")
    template = env.get_template(templatename)
    lighthouse = config.get_config(section="lighthouse")
    hosts = config.get_config(section="hosts")
    groups = config.get_config(section="groups")
    security = config.get_config(section="security")

    is_lighthouse = False
    print("     " + hostname)
    host = build_host(hostname, config)
    lighthouse["address"]=resolveLighthouseAddress(lighthouse["name"], config)
    if host["name"] == lighthouse["name"]:
        is_lighthouse = True
    hostconf = template.render(
        {"lighthouse": lighthouse, "is_lighthouse": is_lighthouse, "host": host}
    )
    directory = config.get_config("output") + "/" + hostname + "/"
    os.makedirs(directory, mode=0o766, exist_ok=True)
    f = open(directory + hostname + ".conf", "w+")
    f.write(hostconf)
    f.close()

def build_systemdUnit(hostname, config):
    env = Environment(
        loader=PackageLoader("nebulamgr", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )

    templatename = config.get_config(section="systemdTemplate")
    unitName = config.get_config(section="unitFilename")
    template = env.get_template(templatename)
    config_file = config.get_config(section="host_config_location") + '/' + hostname + ".conf"
    nebula_bin_location = config.get_config(section="nebula_bin_location")

    print("     Systemd unit file for: " + hostname)
    unitconf = template.render({
        "config_file": config_file,
        "nebula_bin_location": nebula_bin_location
        })

    directory = config.get_config("output") + "/" + hostname + "/" + config.get_config("systemdUnitOutput") + "/"
    os.makedirs(directory, mode=0o766, exist_ok=True)
    f = open(directory + unitName, "w+")
    f.write(unitconf)
    f.close()

def process(args):
    Config = ConfigParser(args.config)
    regen=False
    onlyhost = None
    if args.host is not None:
        onlyhost = args.host
    if args.recert:
        regen=True
    print("Generating configs")
    for host_entry in Config.get_config(section="hosts"):
        for entry in host_entry:
            if onlyhost is None or onlyhost == entry:
                build_conf(entry, Config)
    print("Signing Host Certificates")
    # sign_certs("lighthouse", Config)
    for host_entry in Config.get_config(section="hosts"):
        for entry in host_entry:
            if onlyhost is None or onlyhost == entry:
                sign_certs(entry, Config, regen)

    print("Generating Systemd Unit files")
    for host_entry in Config.get_config(section="hosts"):
        for entry in host_entry:
            if onlyhost is None or onlyhost == entry:
                build_systemdUnit(entry, Config)


def main():
    # Initiate the parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-V", "--version", help="show program version", action="store_true"
    )
    parser.add_argument("--config", help="config file")
    parser.add_argument("--host", help="only process this host")
    parser.add_argument("--recert", help="regenerate the certs", action="store_true", default=False)

    # Read arguments from the command line
    args = parser.parse_args()

    # Check for --version or -V
    if args.version:
        print("This is nebulamgr version 0.2")
    if not args.config:
        print("Please see help option. Missing config file")
    else:
        try:
            process(args)
        except ConfigError as e:
            print(" CONFIG ERROR: " + e.message)
            return
    print("Yay I Win!")


if __name__ == "__main__":
    main()
