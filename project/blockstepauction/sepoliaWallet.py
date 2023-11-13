# script to generate ethereum sepolia wallet
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/17cfb4b3e3cb48399d9584f948071dda'))
account = w3.eth.account.create()
privKey = account._private_key.hex()
pubKey = account.address

print(f'privKey: {privKey}')
print(f'pubKey: {pubKey}')
