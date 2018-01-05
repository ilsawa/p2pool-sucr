import os
import platform

from twisted.internet import defer

from .. import data, helper
from p2pool.util import pack


P2P_PREFIX = '0c6bbdbf'.decode('hex')
P2P_PORT = 9336
ADDRESS_VERSION = 63
SCRIPT_ADDRESS_VERSION = 125
RPC_PORT = 9335
RPC_CHECK = defer.inlineCallbacks(lambda sucrd: defer.returnValue(
            'sucraddress' in (yield sucrd.rpc_help()) and
            not (yield sucrd.rpc_getinfo())['testnet']
        ))
BLOCKHASH_FUNC = lambda data: pack.IntType(256).unpack(__import__('dash_hash').getPoWHash(data))
POW_FUNC = lambda data: pack.IntType(256).unpack(__import__('dash_hash').getPoWHash(data))
BLOCK_PERIOD = 150
SYMBOL = 'SUCR'
CONF_FILE_FUNC = lambda: os.path.join(os.path.join(os.environ['APPDATA'], 'sucrcore') if platform.system() == 'Windows' else os.path.expanduser('~/Library/Application Support/sucrcore/') if platform.system() == 'Darwin' else os.path.expanduser('~/.sucrcore'), 'sucr.conf')
BLOCK_EXPLORER_URL_PREFIX = 'http://sucre.mn.team:3001/block/'
ADDRESS_EXPLORER_URL_PREFIX = 'http://sucre.mn.team:3001/address/'
TX_EXPLORER_URL_PREFIX = 'http://sucre.mn.team:3001/tx/'
SANE_TARGET_RANGE = (2**256//2**32//1000000 - 1, 2**256//2**32 - 1)
DUST_THRESHOLD = 0.001e8
