start: build
	- docker rm -f jupyterhub
	docker run \
		--name jupyterhub \
		--network jupyterhub \
		-e DOCKER_HOST=$(DOCKER_HOST) \
		-e DOCKER_TLS_VERIFY=$(DOCKER_TLS_VERIFY) \
		-e DOCKER_CERT_PATH=/docker_certs \
		-v /docker_certs:/docker_certs \
		-p 8000:8000 \
		-e constraint:node==rogue-leader \
		jupyterhub

build:
	sh -c 'eval $$(docker-machine env rogue-leader); docker build -t jupyterhub hub-inside'

build-swarm:
	# this can only run once
	bash build-swarm

network:
	docker network create --driver overlay jupyterhub

send-certs:
	docker-machine scp -r $(DOCKER_CERT_PATH) rogue-leader:/docker_certs

pull:
	docker pull jupyterhub/singleuser
