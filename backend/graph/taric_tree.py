# backend/graph/taric_tree.py
"""
In-memory TARIC hierarchy as a NetworkX directed graph.
Loaded once at startup from PostgreSQL.
~25k nodes, trivial memory footprint.
"""
import networkx as nx
from db.queries import get_all_taric_nodes

_G: nx.DiGraph | None = None

async def load_taric_graph() -> nx.DiGraph:
    global _G
    nodes = await get_all_taric_nodes()

    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["code"], **{
            "level": n["level"],
            "description": n["description"],
            "chapter_notes": n.get("chapter_notes", ""),
            "subheading_notes": n.get("subheading_notes", ""),
        })
    for n in nodes:
        if n.get("parent_code"):
            G.add_edge(n["parent_code"], n["code"])

    _G = G
    return G


def get_children(code: str) -> list[dict]:
    """All direct children of a code."""
    if _G is None:
        return []
    return [
        {"code": c, **_G.nodes[c]}
        for c in _G.successors(code)
    ]


def get_subtree_leaves(code: str) -> list[dict]:
    """All TARIC10 leaf nodes under a code (any depth)."""
    if _G is None:
        return []
    descendants = nx.descendants(_G, code)
    return [
        {"code": d, **_G.nodes[d]}
        for d in descendants
        if _G.nodes[d].get("level") == "TARIC10"
    ]


def get_sibling_context(code: str) -> list[dict]:
    """Sibling codes at same level (for boundary reasoning)."""
    if _G is None or code not in _G:
        return []
    parents = list(_G.predecessors(code))
    if not parents:
        return []
    siblings = [
        {"code": s, **_G.nodes[s]}
        for s in _G.successors(parents[0])
        if s != code
    ]
    return siblings[:5]


def get_ancestor_chain(code: str) -> list[dict]:
    """Full path from root to this code (for context in prompts)."""
    if _G is None or code not in _G:
        return []
    chain = []
    current = code
    while True:
        preds = list(_G.predecessors(current))
        if not preds:
            break
        parent = preds[0]
        chain.append({"code": parent, **_G.nodes[parent]})
        current = parent
    chain.reverse()
    return chain