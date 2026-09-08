from tree import *
import secrets
from nested_musig2_exec import *
import random

import sys
from pathlib import Path
TEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent.parent

sys.path.insert(0, str(PROJECT_ROOT))
from reference import *

def gen_tree(num_leaves: int) -> Node:
    if num_leaves <= 0:
        raise ValueError("num_leaves must be positive")

    nodes = [Node(str(i)) for i in range(num_leaves)]

    while len(nodes) > 1:
        num_children = random.randint(1, len(nodes))

        children = random.sample(nodes, num_children)

        agg_name = ''
        for child in children:
            agg_name += child.value + '.'
            nodes.remove(child)

        aggregator = Node(agg_name)
        aggregator.children = children
        nodes.append(aggregator)

    nodes[0].is_root = True
    return nodes[0]

for i in range(10):
    num_leaves = random.randint(6,28)
    root = gen_tree(num_leaves)
    msg = secrets.token_bytes(32)

    key_gen_tree(root)
    aggx = get_xonly_pk(root.keyagg_ctx)

    round1(root, aggx, msg)
    v = secrets.randbelow(4)
    tweaks = [secrets.token_bytes(32) for _ in range(v)]
    is_xonly = [secrets.choice([False, True]) for _ in range(v)]
    session_ctx = SessionContext([], [], tweaks, is_xonly, msg)
    round2(root, session_ctx)

    R = root.state_
    assert(verify_r(R, root))

    assert(schnorr_verify(msg, get_xonly_pk(root.keyagg_ctx), root.state_ + root.out_))
