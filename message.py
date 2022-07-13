import json

def msg_hello(node_id):
    return create_msg(node_id, None, 'hello')

# def msg_ack_control(node_id, data):
#     return create_msg(node_id, data, 'ack_control')

def msg_ack_hello(node_id, addr):
    return create_msg(node_id, addr, 'ack_hello')

def msg_peers(node_id, peers):
    return create_msg(node_id, peers, 'peers')

def priv_key_share(value):
    return create_msg('control', value, 'priv_key_share')

def msg_get_peers():
    return create_msg(None, None, 'get_peers')

def msg_init_control():
    return create_msg(None, None, 'init_control')

def msg_send_share(node_id, payload):
    return create_msg(node_id, payload, 'send_share')

def msg_get_share():
    return create_msg(None, None, 'get_share')

def msg_send_info(node_id, info):
    return create_msg(node_id, info, 'info')

def msg_send_pub_k(node_id, pub_k_share):
    return create_msg(node_id, pub_k_share, 'pub_key_share')

def msg_send_peers(node_id, peers):
    return create_msg(node_id, peers, 'send_peers')

def msg_broadcast():
    return create_msg(None, None, 'broadcast')

def msg_init_ack():
    return create_msg(None, None, 'init_ack')

def msg_init(node_id, payload):
    return create_msg(node_id, payload, 'init')

def msg_share(node_id, share):
    return create_msg(node_id, share, 'share')

def create_msg(node_id, msg, msg_type):
    msg = {
        "uuid": node_id,
        "msg": msg,
        "msg_type": msg_type
    }
    msg = json.dumps(msg).encode()
    return msg
