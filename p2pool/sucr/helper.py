import sys
import time

from twisted.internet import defer

import p2pool
from p2pool.sucr import data as sucr_data
from p2pool.util import deferral, jsonrpc

@deferral.retry('Error while checking sucr connection:', 1)
@defer.inlineCallbacks
def check(sucrd, net):
    if not (yield net.PARENT.RPC_CHECK(sucrd)):
        print >>sys.stderr, "    Check failed! Make sure that you're connected to the right sucrd with --sucrd-rpc-port!"
        raise deferral.RetrySilentlyException()
    if not net.VERSION_CHECK((yield sucrd.rpc_getinfo())['version']):
        print >>sys.stderr, '    Sucre version too old! Upgrade to 0.12.2.1 or newer!'
        raise deferral.RetrySilentlyException()

@deferral.retry('Error getting work from sucrd:', 3)
@defer.inlineCallbacks
def getwork(sucrd, net, use_getblocktemplate=True):
    def go():
        if use_getblocktemplate:
            return sucrd.rpc_getblocktemplate(dict(mode='template'))
        else:
            return sucrd.rpc_getmemorypool()
    try:
        start = time.time()
        work = yield go()
        end = time.time()
    except jsonrpc.Error_for_code(-32601): # Method not found
        use_getblocktemplate = not use_getblocktemplate
        try:
            start = time.time()
            work = yield go()
            end = time.time()
        except jsonrpc.Error_for_code(-32601): # Method not found
            print >>sys.stderr, 'Error: Sucre version too old! Upgrade to v0.12.2.1 or newer!'
            raise deferral.RetrySilentlyException()

    if work['transactions']:
        packed_transactions = [(x['data'] if isinstance(x, dict) else x).decode('hex') for x in work['transactions']]
    else:
        packed_transactions = [ ]
    if 'height' not in work:
        work['height'] = (yield sucrd.rpc_getblock(work['previousblockhash']))['height'] + 1
    elif p2pool.DEBUG:
        assert work['height'] == (yield sucrd.rpc_getblock(work['previousblockhash']))['height'] + 1

    # Sucr Payments
    packed_payments = []
    payment_amount = 0
    if 'payee' in work['masternode']:
        g={}
        g['payee']=str(work['masternode']['payee'])
        g['amount']=work['masternode']['amount']
        if g['amount'] > 0:
            payment_amount += g['amount']
            packed_payments.append(g)
    elif work['superblock']:
        for obj in work['superblock']:
                g={}
                g['payee']=str(obj['payee'])
                g['amount']=obj['amount']
                if g['amount'] > 0:
                    payment_amount += g['amount']
                    packed_payments.append(g)

    defer.returnValue(dict(
        version=work['version'],
        previous_block=int(work['previousblockhash'], 16),
        transactions=map(sucr_data.tx_type.unpack, packed_transactions),
        transaction_hashes=map(sucr_data.hash256, packed_transactions),
        transaction_fees=[x.get('fee', None) if isinstance(x, dict) else None for x in work['transactions']],
        subsidy=work['coinbasevalue'],
        time=work['time'] if 'time' in work else work['curtime'],
        bits=sucr_data.FloatingIntegerType().unpack(work['bits'].decode('hex')[::-1]) if isinstance(work['bits'], (str, unicode)) else sucr_data.FloatingInteger(work['bits']),
        coinbaseflags=work['coinbaseflags'].decode('hex') if 'coinbaseflags' in work else ''.join(x.decode('hex') for x in work['coinbaseaux'].itervalues()) if 'coinbaseaux' in work else '',
        height=work['height'],
        last_update=time.time(),
        use_getblocktemplate=use_getblocktemplate,
        latency=end - start,
        payment_amount = payment_amount,
        packed_payments = packed_payments,
    ))

@deferral.retry('Error submitting primary block: (will retry)', 10, 10)
def submit_block_p2p(block, factory, net):
    if factory.conn.value is None:
        print >>sys.stderr, 'No sucrd connection when block submittal attempted! %s%064x' % (net.PARENT.BLOCK_EXPLORER_URL_PREFIX, sucr_data.hash256(sucr_data.block_header_type.pack(block['header'])))
        raise deferral.RetrySilentlyException()
    factory.conn.value.send_block(block=block)

@deferral.retry('Error submitting block: (will retry)', 10, 10)
@defer.inlineCallbacks
def submit_block_rpc(block, ignore_failure, sucrd, sucrd_work, net):
    if sucrd_work.value['use_getblocktemplate']:
        try:
            result = yield sucrd.rpc_submitblock(sucr_data.block_type.pack(block).encode('hex'))
        except jsonrpc.Error_for_code(-32601): # Method not found, for older litecoin versions
            result = yield sucrd.rpc_getblocktemplate(dict(mode='submit', data=sucr_data.block_type.pack(block).encode('hex')))
        success = result is None
    else:
        result = yield sucrd.rpc_getmemorypool(sucr_data.block_type.pack(block).encode('hex'))
        success = result
    success_expected = net.PARENT.POW_FUNC(sucr_data.block_header_type.pack(block['header'])) <= block['header']['bits'].target
    if (not success and success_expected and not ignore_failure) or (success and not success_expected):
        print >>sys.stderr, 'Block submittal result: %s (%r) Expected: %s' % (success, result, success_expected)

def submit_block(block, ignore_failure, factory, sucrd, sucrd_work, net):
    submit_block_rpc(block, ignore_failure, sucrd, sucrd_work, net)
    submit_block_p2p(block, factory, net)
