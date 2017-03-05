# JupyterHub config file for Docker Swarm
# This time, the Hub is on the host.

from dockerspawner import DockerSpawner
from tornado import gen

c.JupyterHub.spawner_class = DockerSpawner
c.DockerSpawner.use_docker_client_env = True
# tell containers to listen on all IPs
c.DockerSpawner.container_ip = '0.0.0.0'

# hub_ip needs to be accessible to the single-user servers.
# Since our test is all using virtualbox,
# I'm using the vbox ip.
# In the real world, this might be `eth0` or some other public or LAN interface.
import netifaces
device = 'vboxnet0'
c.JupyterHub.hub_ip = netifaces.ifaddresses(device)[netifaces.AF_INET][0]['addr']
