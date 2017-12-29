from p2pool.sucr import networks

PARENT = networks.nets['sucr']
SHARE_PERIOD = 25
CHAIN_LENGTH = 24*60*60//25
REAL_CHAIN_LENGTH = 24*60*60//25
TARGET_LOOKBEHIND = 100
SPREAD = 10
IDENTIFIER = '1bfe429c611a3651'.decode('hex')
PREFIX = '1bfe429c624b6352'.decode('hex')
COINBASEEXT = '2f5032506f6f6c2d535543522f'.decode('hex')
P2P_PORT = 19338
MIN_TARGET = 4
MAX_TARGET = 2**256//2**20 - 1
PERSIST = True
WORKER_PORT = 9339
BOOTSTRAP_ADDRS = 'crypto.office-on-the.net siberia.mine.nu'.split(' ')
ANNOUNCE_CHANNEL = '#p2pool-sucr'
VERSION_CHECK = lambda v: v >= 120201
