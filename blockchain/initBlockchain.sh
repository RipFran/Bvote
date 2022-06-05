#!/bin/bash

#INIT BLOCKCHAINS
python3 blockchain.py -p 4000 -i $1 &
python3 blockchain.py -p 4001 -i $1 &
python3 blockchain.py -p 4002 -i $1 &
python3 blockchain.py -p 4003 -i $1 &


#Comunicate Blockchains 
curl -X POST -s http://localhost:4000/nodes/register -H "Content-Type: application/json" -d '{"nodes":"127.0.0.1:4003,127.0.0.1:4001,127.0.0.1:4002"}'
curl -X POST -s http://localhost:4001/nodes/register -H "Content-Type: application/json" -d '{"nodes":"127.0.0.1:4000,127.0.0.1:4003,127.0.0.1:4002"}'
curl -X POST -s http://localhost:4002/nodes/register -H "Content-Type: application/json" -d '{"nodes":"127.0.0.1:4000,127.0.0.1:4001,127.0.0.1:4003"}'
curl -X POST -s http://localhost:4003/nodes/register -H "Content-Type: application/json" -d '{"nodes":"127.0.0.1:4000,127.0.0.1:4001,127.0.0.1:4002"}'


