####Iroha Docker Compose


#How To Run:

##Iroha Distributed Ledger

* Ubuntu 16 or 18
* Docker + Docker Compose

clone report locally

Please ensure you are in the root directory of the project folder.
This will be the same location as the docker-compose.yaml file

Amend config as required.

open a terminal in Bash

* docker-compose up -d (Runs in background)
* docker-compose up Runs with Interactive Logs

verify that both Iroha & Postgres are running with docker ps
the current container names should appear

To Tear Down or Restart.

docker-compose down
or
docker-compose restart

Note that in ./iroha/entrypoint.sh is a bash command which starts Irohas daemon.
For development and easy tear down, --overwrite-ledger flags are provided
This will delete the existing blockstore each time the stack is started.

irohad --genesis_block genesis.block --config config.docker --keypair_name $KEY --overwrite-ledger

To persist storage.

remove --overwrite-ledger flag. The last line of the bash script will look like this:

irohad --genesis_block genesis.block --config config.docker --keypair_name $KEY

#Advanced Config

If launching multiple nodes, the following enviroment variables will need to be amended accordingly.

Please ensure that the files match their expected naming convetions else the Daemon will not find the correct keys and cannot start the ledger

services:
  iroha:
    image: hyperledger/iroha:master # pulls latest build
    container_name: iroha-testnet
    depends_on:
      - some-postgres
    restart: always
    tty: true
    environment:
      - KEY=keys/node0 - Change to the corrosding key pair location, and name. node0 looks for
      node0.pub & node0.priv
      - IROHA_POSTGRES_HOST=some-postgres
      - IROHA_POSTGRES_PORT=5432
      - IROHA_POSTGRES_USER=postgres
      - IROHA_POSTGRES_PASSWORD=mysecretpassword - Change this for production, as well as on all of the corrosponding config files
    entrypoint:
      - /opt/iroha_data/entrypoint.sh
    networks:
      - iroha
    volumes:
      - ./iroha:/opt/iroha_data
    ports:
      - 50051:50051 [Default gRPC port for Iroha, if this port is occupied change it accordingly. Note that all commands & queries will need to Correct Ports and would need to know this in advance for commiting transactions. This is exposed to the public. Normal security mesures will need to be implemented]