# JupyterHub config file for Docker Swarm
# In this case, the Hub has the name 'jupyterhub' and is
# on the 'jupyterhub' overlay network.

from dockerspawner import DockerSpawner

c.JupyterHub.spawner_class = DockerSpawner
# we are passing swarm environment variables in the start command
c.DockerSpawner.use_docker_client_env = True

# The Hub has the hostname 'jupyterhub' on the docker network.
# It will be listening on all ips for internal connections
c.JupyterHub.hub_ip = '0.0.0.0'
c.DockerSpawner.hub_ip_connect = 'jupyterhub'

# these three lines tell the single-user containers
# to join the 'jupyterhub' overlay network,
# and use the container's ip on that network
# when telling the Hub where to find it.
c.DockerSpawner.network_name = 'jupyterhub'
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.extra_host_config = {
    'network_mode': 'jupyterhub',
}


from tornado import gen
from jupyterhub.auth import Authenticator

# dummy authenticator for testing. Use a real one (ideally OAuth, etc.)
the_password = 'a secret'
class DummyAuthenticator(Authenticator):
    @gen.coroutine
    def authenticate(self, handler, data):
        if data['password'] == the_password:
            return data['username']

c.JupyterHub.authenticator_class = DummyAuthenticator
