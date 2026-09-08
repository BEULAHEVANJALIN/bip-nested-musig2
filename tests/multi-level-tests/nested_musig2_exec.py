from tree import Node
import secrets

from pathlib import Path
import sys
TEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from reference import *

def key_gen_tree(node: Node):
    if node.is_leaf():
        node.sk = secrets.token_bytes(32)
        node.pk = individual_pk(node.sk)
    else:
        for w in node.children:
            key_gen_tree(w)
        child_pks =  key_sort([w.pk for w in node.children])
        node.keyagg_ctx = key_agg(child_pks)
        node.pk = PlainPk(cbytes(node.keyagg_ctx.Q))


def round1(node: Node, aggpk: XonlyPk = None, msg: bytes = None, extra_in = None):
    if node.is_leaf():
        (secnonce, pubnonce) = nonce_gen(node.sk, node.pk, aggpk, msg, extra_in)
        node.out = pubnonce
        node.state = secnonce
    else:
        for w in node.children:
            round1(w, aggpk, msg, extra_in)
        node.out_internal = nonce_agg([w.out for w in node.children])
        node.out = nonce_agg_ext(node.out_internal, node.keyagg_ctx.Q)

def round2(node: Node, session_ctx: SessionContext, rand:bytes = None):
    if node.is_leaf():
        final_nonce, psig = sign(node.state, node.sk, session_ctx)
        node.out_ = psig
        node.state_ = final_nonce
    else:
        nonce_path, pk_tree, tweaks, is_xonly, msg = session_ctx
        for w in node.children:
            siblings = [u.pk for u in node.children if u.pk != w.pk]
            session_ctx_ = SessionContext(nonce_path + [node.out_internal], pk_tree + [siblings], tweaks, is_xonly, msg)
            round2(w, session_ctx_, rand)

        node.state_ = node.children[0].state_ # same for every node
        psigs = [w.out_ for w in node.children]

        # Aggregating signatures of the children
        if node.is_root:
            s = partial_sig_agg(psigs, node.state_, session_ctx, node.keyagg_ctx)
        else:
            s = partial_sig_agg(psigs, node.state_)
        node.out_ = s

def verify_r(R: bytes, node: Node):
    if node.is_leaf():
        if R != node.state_:
            print(node.value + " failed to verify R")
            print(node.state_.hex().upper())
            return False
        else:
            return True
    else:
        for w in node.children:
            if not verify_r(R, w):
                return False
        return True
