import argparse
import os
import subprocess

from jinja2 import Environment, PackageLoader, select_autoescape

from configparser import ConfigParser


def build_host(hostname, config):
    if hostname == "lighthouse":
        host = {"name": hostname, "groups": [], "outbound": [], "inbound": []}
    else:
        for host_entry in config.get_config(section="hosts"):
            for name in host_entry:
                if hostname == name:
                    host = host_entry[hostname]
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


def sign_certs(hostname, config):
    print("     " + hostname)
    if hostname == "lighthouse":
        host = config.get_config("lighthouse")
    else:
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
    result = subprocess.run(args, cwd=workdir, capture_output=True)
    if result.returncode > 0:
        print(" Cert gen failed with return code " + str(result.returncode))
        print(result.stdout.decode("utf-8"))
        print(result.stderr.decode("utf-8"))


def process(args):
    env = Environment(
        loader=PackageLoader("nebulamgr", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    Config = ConfigParser(args.config)
    templatename = Config.get_config(section="template")
    template = env.get_template(templatename)
    lighthouse = Config.get_config(section="lighthouse")
    hosts = Config.get_config(section="hosts")
    groups = Config.get_config(section="groups")
    security = Config.get_config(section="security")

    #
    # process lighthouse
    #
    print("generating configs")
    print("     lighthouse")
    host = build_host("lighthouse", Config)
    lighthouseconf = template.render(
        {"lighthouse": lighthouse, "is_lighthouse": "true", "host": host}
    )
    directory = Config.get_config("output") + "/" + host["name"] + "/"
    os.makedirs(directory, mode=0o766, exist_ok=True)
    f = open(directory + host["name"]+".conf", "w+")
    f.write(lighthouseconf)
    f.close()
    for host_entry in Config.get_config(section="hosts"):
        for entry in host_entry:
            print("     " + entry)
            host = build_host(entry, Config)
            hostconf = template.render(
                {"lighthouse": lighthouse, "is_lighthouse": "false", "host": host}
            )
            directory = Config.get_config("output") + "/" + entry + "/"
            os.makedirs(directory, mode=0o766, exist_ok=True)
            f = open(directory + "main.conf", "w+")
            f.write(hostconf)
            f.close()

    print("Signing Host Certificates")
    sign_certs("lighthouse", Config)
    for host_entry in Config.get_config(section="hosts"):
        for entry in host_entry:
            sign_certs(entry, Config)
    # print(lighthouseconf)
    # outbound:
    # - port: any
    #   proto: any
    #   host: any
    # inbound:
    #     # Allow icmp between any nebula hosts
    #     - port: any
    #     proto: icmp
    #     host: any


def main():
    # Initiate the parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-V", "--version", help="show program version", action="store_true"
    )
    parser.add_argument("--config", help="config file")

    # Read arguments from the command line
    args = parser.parse_args()

    # Check for --version or -V
    if args.version:
        print("This is myprogram version 0.1")
    else:
        process(args)

    print("Yay I Win!")


if __name__ == "__main__":
    main()
