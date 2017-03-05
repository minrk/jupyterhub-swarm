# Running JupyterHub with Docker Swarm

This is a record of my experiments with running JupyterHub with docker swarm, set up via `docker-machine`.
Just about all of the configuration needed is networking-related.

## Bootstrap swarm

Following [the docs](https://docs.docker.com/engine/userguide/networking/get-started-overlay/#create-a-swarm-cluster), I created a swarm with `docker-machine`.
I'm using macOS with `docker-machine` from [Docker for Mac](https://docs.docker.com/docker-for-mac/).
I started with the virtualbox driver, but since I'm on hotel wifi, I switched to `rackspace`.
The [`build-swarm`](build-swarm) script is how I created the swarm with three nodes.


### Check the swarm:

I got this from

```
eval $(docker-machine env --swarm rogue-leader)
docker info
```

```
Containers: 5
 Running: 5
 Paused: 0
 Stopped: 0
Images: 10
Server Version: swarm/1.2.6
Role: primary
Strategy: spread
Filters: health, port, containerslots, dependency, affinity, constraint, whitelist
Nodes: 2
 rogue-leader: 104.130.1.233:2376
  └ ID: MVDM:FUZI:RBLO:HDIU:7D35:2NPQ:GLSS:RL5Y:QOPS:SJBN:6QEK:W3QU
  └ Status: Healthy
  └ Containers: 3 (3 Running, 0 Paused, 0 Stopped)
  └ Reserved CPUs: 0 / 1
  └ Reserved Memory: 0 B / 1.016 GiB
  └ Labels: kernelversion=4.4.0-45-generic, operatingsystem=Ubuntu 16.04.1 LTS, provider=rackspace, storagedriver=aufs
  └ UpdatedAt: 2017-03-05T06:49:30Z
  └ ServerVersion: 17.03.0-ce
 rogue-one: 104.130.11.39:2376
  └ ID: FNO3:YWNK:ZPI7:3NI2:VAO3:RA5G:FDHD:EW3L:PBY4:R3Z3:PP3J:ZX4A
  └ Status: Healthy
  └ Containers: 2 (2 Running, 0 Paused, 0 Stopped)
  └ Reserved CPUs: 0 / 1
  └ Reserved Memory: 0 B / 1.016 GiB
  └ Labels: kernelversion=4.4.0-45-generic, operatingsystem=Ubuntu 16.04.1 LTS, provider=rackspace, storagedriver=aufs
  └ UpdatedAt: 2017-03-05T06:49:42Z
  └ ServerVersion: 17.03.0-ce
Plugins:
 Volume:
 Network:
Swarm:
 NodeID:
 Is Manager: false
 Node Address:
Kernel Version: 4.4.0-45-generic
Operating System: linux
Architecture: amd64
CPUs: 2
Total Memory: 2.032 GiB
Name: 830658b3c773
Docker Root Dir:
Debug Mode (client): false
Debug Mode (server): false
WARNING: No kernel memory limit support
Experimental: false
Live Restore Enabled: false
```

From this point on, we will be using the swarm, which in my case means:

```bash
eval $(docker-machine env --swarm rogue-leader)
```


## Round 1: Hub in the swarm

Since I'm running from my laptop which isn't on the public internet,
I can't run the Hub locally because the swarm nodes can't connect back to the laptop.
So I elected to run the Hub in the swarm as well, confined to the `rogue-leader` node.

Since I'm using swarm and the Hub needs to talk to the swarm,
I need to get the credentials from my laptop to the hub node.
I used `docker-machine scp` and a volume to do this,
but it could also be done by copying the files into the `hub` directory and putting them in the container with `ADD`:

```bash
docker-machine scp -r $(DOCKER_CERT_PATH) rogue-leader:/docker_certs
```

The next thing to do was to create the `jupyterhub` overlay network:

```bash
docker network create --driver overlay jupyterhub
```

And pull our singleuser image. I'm using the default:

```bash
docker pull jupyterhub/singleuser
```

In our [jupyterhub_config.py](hub-inside/jupyterhub_config.py),
most of the configuration is telling everything how to connect on the network:

1. jupyterhub and single-user servers are all on the `jupyterhub` overlay network
2. Tell single-user servers to connect to the hub by hostname
3. tell DockerSpawner to use the container ip for the `jupyterhub` network

I had to make sure to build the jupyterhub image on rogue-leader, which means *not* using the swarm config.
I couldn't figure out how to use swarm while ensuring that `docker build` would produce an image on the desired node.
It would work the first time, but subsequent rebuilds would run on different nodes.
There must be a better way.

```bash
eval $(docker-machine env rogue-leader)
docker build -t jupyterhub hub-inside
```

### Run the Hub

It takes quite a few arguments to run the hub how we want it. We want to:

1. pin it to a particular node
2. put it on the jupyterhub network
3. mount the swarm credentials directory
4. pass the swarm environment variables

This amounts to:

```bash
docker run \
    --name jupyterhub \
    --network jupyterhub \
    -e DOCKER_HOST=$DOCKER_HOST \
    -e DOCKER_TLS_VERIFY=$DOCKER_TLS_VERIFY \
    -e DOCKER_CERT_PATH=/docker_certs \
    -v /docker_certs:/docker_certs \
    -p 8000:8000 \
    -e constraint:node==rogue-leader \
    jupyterhub
```


## Round 2: Hub outside the swarm

This one seems trickier, since we need to make sure the Hub can see the containers.
