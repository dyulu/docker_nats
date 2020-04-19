all: build-nats run-nats

build-nats:
	docker build -t nats_server_go_sub -f Dockerfile_nats_server_go_sub .
	docker build -t nats_py_pub -f Dockerfile_nats_py_pub .

run-nats:
	docker network create nats_network
	docker run -d --name nats_py_pub --network nats_network --env NATS_SERVER=nats_server_go_sub -p 5000:5000 nats_py_pub
	docker run -it --name nats_server_go_sub --network nats_network nats_server_go_sub

clean:
	docker stop nats_server_go_sub nats_py_pub
	docker rm nats_server_go_sub nats_py_pub
	docker rmi nats_server_go_sub nats_py_pub
	docker network rm nats_network

test-start-nats-server-sub:
	${GOPATH}/bin/nats-server &
	sleep 1
	go run ${GOPATH}/src/github.com/nats-io/nats.go/examples/nats-sub/main.go mem_usage_fault

test-start-nats-pub:
	python3 src/MemUsageMonitor.py

