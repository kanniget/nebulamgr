#
#   See Nebula VPN here   https://github.com/slackhq/nebula
#

- Create all the required configurations for the Nebula VPN from a central location

- Create a config file similar to `nebulamgr.yaml`

- Generate your nebula CA certs if you already haven't

- Run `python nebularmgr.py --config=\<your conf file\>`

This will rebuild the config based on the `template.jinja` file (as specified in the conf file above) 

If you want to replace the already generated certs add the command line option `--recert`

If you later add a host and dont want to regenerate everything then add `--host <hostname>`

The config and keys are generated into a seperate subdirectory for each host specificed in the config file
