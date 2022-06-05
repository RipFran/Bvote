"""
sudo apt install libmariadb3 libmariadb-dev
python3 -m pip install pycryptodome
pip3 install mariadb
"""

import hashlib
from signal import signal
from Crypto.Hash import SHA256
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import pkcs1_15
import requests
from flask import Flask, jsonify, request
import binascii
import mariadb

class Blockchain:
    def __init__(self):
        self.current_transactions = []
        self.orphans= []
        self.forks= [[[],[]]]
        self.nodes = set()
        self.recipients=[]
        # inicializar con la base de datos
        self.chain = [[],[]]
        # Create the genesis block
        self.new_block(previous_hash='1', proof=100,transactions=self.current_transactions,timestamp=0)
    
    def initialize(self, id):
        self.chain[1]=self.init_senders(id)
        self.recipients=self.init_recipients(id)
    
    def getrecipient(self,id,entidad):
        try:
            conn = mariadb.connect(
                user="alumne",
                password="alumne",
                host="127.0.0.1",
                port=3306,
                database=id
            )
        
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
        cur = conn.cursor()
        
        cur.execute(
            "SELECT pk FROM recipientsPK where entidad = "+ entidad)

        for pk in cur:
            return pk    

        
    def mine(self):
        last_block = self.last_block
        timestamp=time()
        previous_hash = blockchain.hash(last_block)
        proof = blockchain.proof_of_work(previous_hash,timestamp)

        block = blockchain.new_block(proof, previous_hash,blockchain.current_transactions,timestamp)
        return block

    def init_recipients(self,id):
        try:
            conn = mariadb.connect(
                user="alumne",
                password="alumne",
                host="127.0.0.1",
                port=3306,
                database=id
            )

        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
        cur = conn.cursor()
        
        cur.execute(
            "SELECT pk FROM recipientsPK")
        
        tmp=[]
        for (pk) in cur: tmp.append(pk)
        return tmp

    def init_senders(self,id):
        try:
            conn = mariadb.connect(
                user="alumne",
                password="alumne",
                host="127.0.0.1",
                port=3306,
                database=id
            )

        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
        cur = conn.cursor()
        
        cur.execute(
            "SELECT pk FROM sendersPK")
        
        tmp=[]
        for (pk) in cur:
            tmp.append(pk[0])
        return tmp


    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: Address of node. Eg. 'http://192.168.0.5:5000'
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def choose_chain(self):
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain[0])
        chains=[self.chain[0]]
        times=[1]
        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if self.valid_chain(chain):
                    chains.append(chain)
                    if len(chain) > max_length:
                        max_length = length
                        new_chain = chain
        max_count=1

        for ch in chains:
            count=chains.count(ch)
            if count>len(chains)/2:
                return ch
            if count>max_count:
                max_count=count
                new_chain=ch
                max_length=len(ch)
            if count==max_count and len(ch)>max_length:
                max_length=len(ch)
                new_chain=ch

        return new_chain

    def valid_transaction(self, transaction):
        signature = self.encode_signature(transaction['signature'])
        sender=RSA.import_key(transaction['sender'])

        if (not (transaction['sender'] in self.chain[1])) or (not (self.getrecipient(id,transaction['recipient']) in self.recipients)):
            return False

        message='signature'
        h=SHA256.new(message.encode())

        try:
            pkcs1_15.new(sender).verify(h, signature)

        except (ValueError, TypeError):
            print("Error en la validación de las firmas")
            return False
        return True

    def encode_signature(self, signature):
        nums = signature.split(',')
        sig = bytes()
        for num in nums:
            sig+=int(num).to_bytes(1,'big')
        return sig

    

    def valid_block(self, block):
        if len(self.chain[0])==0: return True
        if not self.valid_proof(block['proof'], block['previous_hash'], block['timestamp']):
            return False
        if self.repeated_block(block):
            return False
        for trans in block['transactions']:
            if not self.valid_transaction(trans):
                return False
        return True

    def repeated_block(self, block):
        for b in self.chain[0]:
            if b==block: return True
            
        for b in self.orphans:
            if b==block: return True
            
        for fork in self.forks:
            for b in fork:
                if b==block: return True
        
        return False

    def repeated_transaction(self, sender):      
        for trans in self.current_transactions:
            if trans['sender']==sender:
                return True
        return False


    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(block['proof'], block['previous_hash'], block['timestamp']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain[0])

        for fork in self.forks:
            length = len(fork[0])
                # Check if the length is longer and the chain is valid
            if length > max_length:
                max_length = length
                new_chain = fork

        for fork in self.forks:
            if len(fork[0])<max_length-2:
                self.forks.remove(fork)
        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            if len(self.chain[0])>=max_length-2:
                self.forks.append(self.chain)
            self.chain = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash, transactions, timestamp):
        self.resolve_conflicts()
        block = {
            'timestamp': timestamp,
            'transactions': transactions,
            'proof': proof,
            'previous_hash': previous_hash,
        }
        if not self.valid_block(block):
            return {}
        
        # Reset the current list of transactions
        self.clean_transactions(transactions)
        search=self.search_in_chain(self.chain,block)
        if search==1:
            self.chain[1]=self.clean_senders(self.chain[1],block)
            self.chain[0].append(block)
            self.traverse_orphans(self.chain,self.hash(block))
        elif search==2:
            self.traverse_orphans(self.forks[-1],self.hash(block))
        else:
            parents=False
            for fork in self.forks:
                search=self.search_in_chain(fork,block)
                if search==1:
                    fork[1]=self.clean_senders(fork[1],block)
                    fork[0].append(block)
                    self.traverse_orphans(fork,self.hash(block))
                    parents=True
                    break
                elif search==2:
                    self.traverse_orphans(self.forks[-1],self.hash(block))
                    parents=True
                    break
            if not parents:
                self.orphans.append(block)
        self.spread_block(block)
        return block
        
    def results(self):
        try:
            conn = mariadb.connect(
                user="alumne",
                password="alumne",
                host="127.0.0.1",
                port=3306,
                database=id
            )

        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
        cur = conn.cursor()
        
        cur.execute(
            "SELECT entidad FROM recipientsPK")
        
        tmp=[]
        for (pk) in cur: tmp.append(pk)

        results = {}
        for val in tmp:
            results[val[0]] = 0
                    
        for b in self.chain[0]:
            for trans in b['transactions']:
                results[trans['recipient']]+=1
        return results
        
    def spread_block(self, block):
        headers = {'content-type': 'application/json'}
        payload ={'proof': block['proof'],'previous_hash': block['previous_hash'], 'transactions': block['transactions'], 'timestamp': block['timestamp']}
        payload = json.dumps(payload)
        for node in self.nodes:
            requests.post('http://'+node+'/newblock',data=payload,headers=headers)

    def search_in_chain(self, ch, block):
        if len(self.chain[0])==0:
            return 1
        if block['previous_hash']==self.hash(ch[0][-1]):
            return 1
        if len(ch[0])>1:
            if block['previous_hash']==self.hash(ch[0][-2]):
                temp=ch[0:len(ch)-2]
                temp.append(block)
                temp2=self.clean_senders(ch[1],block)
                self.forks.append([temp,temp2])
                return 2
        return 3

    def traverse_orphans(self, ch, hash):
        for b in self.orphans:
            if b['previous_hash']==hash:
                self.orphans.remove(b)
                ch[0].append(b)
                ch[1]=self.clean_senders(ch[1],b)
                self.traverse_orphans(ch,self.hash(b))
                break

    def clean_transactions(self, transactions):
        self.current_transactions = [x for x in self.current_transactions if x not in transactions]

    def clean_senders(self,previous_senders, block):
        for trans in block['transactions']:
            previous_senders.remove(trans['sender'])
        return previous_senders
    
        

    def new_transaction(self, sender, recipient, signature):
        transaction={
            'sender': sender,
            'recipient': recipient,
            'signature': signature,
        }
        if self.repeated_transaction(sender): return -1
        if not self.valid_transaction(transaction):
            return -1
        self.current_transactions.append(transaction)
        if(len(self.current_transactions) == 10):
            self.mine()
        return 0

    @property
    def last_block(self):
        return self.chain[0][-1]

    @staticmethod
    def hash(block):

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, previous_hash, timestamp):
        proof = 0
        while self.valid_proof(proof,previous_hash,timestamp) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(proof, previous_hash, timestamp):
        guess = f'{proof}{previous_hash}{timestamp}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()

@app.route('/results', methods=['GET'])
def results():
    results = blockchain.results()
    return jsonify(results), 200

@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    block = blockchain.mine()
    
    response = {
        'message': "New Block Forged",
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'signature']
    if not all(k in values for k in required):
        return 'Missing values', 400
    # Create a new Transaction
    
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['signature'])

    if index==-1:
        response={'Message': 'Error'}
        return jsonify(response), 400   

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain[0],
        'length': len(blockchain.chain[0]),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():

    values = request.get_json()

    nodes = values.get('nodes')

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    arraynodes = nodes.split(",")
  
    for node in arraynodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    chain= blockchain.choose_chain()

    response = {
        'chain': chain
    }

    return jsonify(response), 200

@app.route('/nodes/list', methods=['GET'])
def getNodes():
    response={'nodes':str(blockchain.nodes)}
    return jsonify(response), 200

@app.route('/newblock', methods=['POST'])
def newblock():
    values= request.get_json()
    
    required=['proof', 'previous_hash', 'timestamp', 'transactions']
    if not all (k in values for k in required):
        return "missing values", 400
    block = blockchain.new_block(values['proof'], values['previous_hash'], values['transactions'], values['timestamp'])
    
    if block == {}:
        response = {'message': 'invalid block'}
        return jsonify(response), 400
    
    response = {'message': 'block add to the blockchain'}
    return jsonify(response), 201

@app.route('/validate', methods=['GET'])
def validate():
    if blockchain.valid_chain(blockchain.chain):
        return "The stored chain is valid\n", 200
    else:
        return "The stored chain is not valid\n", 200

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-i', '--identifier',default="none",type=str,help='Data base identifier')
    args = parser.parse_args()
    port = args.port
    id=args.identifier

    if id=="none":
        print("Identifier mandatory. Usage: python3 blockchain.py -i database_identifier")
        exit(1)
    blockchain.initialize(id)
    app.run(host='0.0.0.0', port=port)




