import binascii
from iroha import IrohaCrypto as ic
from iroha import Iroha, IrohaGrpc
from iroha.primitive_pb2 import can_set_my_account_detail, can_transfer
import sys
import json
import os
import asyncio

IROHA_HOST_ADDR = os.getenv('IROHA_HOST_ADDR', '127.0.0.1')
IROHA_PORT = os.getenv('IROHA_PORT', '50051')
ADMIN_ACCOUNT_ID = os.getenv('ADMIN_ACCOUNT_ID', 'admin@test')
ADMIN_PRIVATE_KEY = admin_private_key = os.getenv('ADMIN_PRIVATE_KEY', 'f101537e319568c765b2cc89698325604991dca57b9716b58016b253506cab70')

iroha = Iroha(ADMIN_ACCOUNT_ID)
net = IrohaGrpc('{}:{}'.format(IROHA_HOST_ADDR, IROHA_PORT),timeout=None)
    
async def send_transaction_and_print_status(transaction):
    global net
    hex_hash = binascii.hexlify(ic.hash(transaction))
    print('Transaction hash = {}, creator = {}'.format(
        hex_hash, transaction.payload.reduced_payload.creator_account_id))
    net.send_tx(transaction)
    for status in net.tx_status_stream(transaction):
        print(status)

async def send_transaction(transaction):
    global net
    hex_hash = binascii.hexlify(ic.hash(transaction))
    print('Transaction hash = {}, creator = {}'.format(
        hex_hash, transaction.payload.reduced_payload.creator_account_id))
    net.send_tx(transaction)

def add_asset_to_admin(asset_id, qty):
    global iroha
    """
    Add asset supply and assign to 'admin'
    """
    tx = iroha.transaction([
        iroha.command('AddAssetQuantity',
                      asset_id=asset_id, amount=qty)
    ])
    ic.sign_transaction(tx, admin_private_key)
    send_transaction_and_print_status(tx)

def create_and_issue_new_asset(asset,domain,precision,qty,account_id,description):
    global iroha
    user_tx = iroha.transaction(
        [iroha.command('CreateAsset', asset_name=asset,
            domain_id=domain, precision=precision)]    )
    ic.sign_transaction(user_tx, admin_private_key)
    send_transaction_and_print_status(user_tx)
    asset_id = asset + '#' + domain
    add_asset_to_admin(asset_id=asset_id,qty=qty)
    transfer_asset_from_admin(account_id,asset_id,description,qty)
    set_account_detail(asset_id,description)

def transfer_asset_from_admin(recipient,asset_id,description,qty):
    user_tx = iroha.transaction([
        iroha.command('TransferAsset', src_account_id='admin@test', dest_account_id=recipient,
                      asset_id=asset_id, description=description, amount=qty)])
    ic.sign_transaction(user_tx, admin_private_key)
    send_transaction_and_print_status(user_tx)

def create_users(user_name,domain,user_public_key):
    """
    register new user, grant permission to admin and set password & plenteum address
    """
    init_cmds = [
        iroha.command('CreateAccount', account_name=user_name, domain_id=domain,
                      public_key=user_public_key)
    ]
    init_tx = iroha.transaction(init_cmds,creator_account='admin@test')
    ic.sign_transaction(init_tx, admin_private_key)
    send_transaction_and_print_status(init_tx)

async def create_accounts(i):
        private_key = ic.private_key()
        public_key = ic.derive_public_key(private_key)
        user_name = str(i)
        init_cmds = [
            iroha.command('CreateAccount', account_name=user_name, domain_id='test',
                        public_key=public_key)
        ]
        init_tx = iroha.transaction(init_cmds,creator_account='admin@test')
        ic.sign_transaction(init_tx, admin_private_key)
        await send_transaction(init_tx)

async def accounts_load_test():
    import time

    start_time = time.time()
    cpu_start_time = time.process_time()
    
    for i in range(1000):
        await create_accounts(i=i)
    total_real_time = time.time() - start_time
    total_cpu_time = time.process_time() - cpu_start_time
    print(total_cpu_time)

def create_domain(domain):
    """
    register non existing/new domain on network
    """
    commands = [
        iroha.command('CreateDomain', domain_id=domain, default_role='user'),
    ]
    tx = ic.sign_transaction(
        iroha.transaction(commands), admin_private_key)
    send_transaction_and_print_status(tx)

def add_signatory():
    pass

def get_blocks():
    """
    Subscribe to blocks stream from the network
    :return:
    """
    query = iroha.blocks_query()
    ic.sign_query(query, admin_private_key)
    for block in net.send_blocks_stream_query(query):
        print('The next block arrived:', block)

def set_account_detail(key,value):
    """
    Set account detail key value
    """
    tx = iroha.transaction([
        iroha.command('SetAccountDetail', key=key, value=value)
    ])
    ic.sign_transaction(tx, admin_private_key)
    send_transaction_and_print_status(tx)

def get_asset_info(asset_id):
    """
    Get asset info
    :return:
    """
    query = iroha.query('GetAssetInfo', asset_id=asset_id)
    ic.sign_query(query, admin_private_key)
    response = net.send_query(query)
    data = response.asset_response.asset
    print('Asset id = {}, precision = {}'.format(data.asset_id, data.precision))

def get_account_assets(account_id):
    """
    List all the assets of user@domain
    """
    query = iroha.query('GetAccountAssets', account_id=account_id)
    ic.sign_query(query, admin_private_key)

    response = net.send_query(query)
    data = response.account_assets_response.account_assets
    return data

def get_tx_history(account_id,total):
    """
    List total number of tx details of user@domain
    """
    query = iroha.query('GetAccountTransactions', account_id=account_id, page_size=total)
    ic.sign_query(query, admin_private_key)

    response = net.send_query(query)
    return response
    
def get_user_details(account_id):
    """
    Get all the kv-storage entries for user@domain
    """
    query = iroha.query('GetAccountDetail', account_id=account_id)
    ic.sign_query(query, admin_private_key)
    response = net.send_query(query)
    data = response.account_detail_response
    user = json.loads(str(data.detail))
    print('Account id = {}, details = {}'.format(account_id, data.detail))
    return user