#
#   See Nebula VPN here   https://github.com/slackhq/nebula
#
#
Create all the required configs from the Nebula VPN from a central location/

Create a config file similar to nebulamgr.yaml

generate your nebula ca certs if you already haven't

python nebularmgr.py --config=\<your conf file\>

this will rebuild the config based on the template.jinja file ( as specified in the conf file above....   ) 

If you want to replace the already generated certs add the command line option --recert

if you later add a host and dont want to regenerate everything then add --host <hostname> 


The configs etc are generated into a seperate subdirectory for each host listed in the config file below the location specified in the config file....

