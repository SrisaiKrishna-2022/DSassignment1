#!/usr/bin/env python3
import sys
import json
import random
import os


def generate_random_graph(num_nodes: int, edge_prob: float = 0.3) -> dict:
    """
    Generate a random undirected graph as an adjacency list.
    Nodes are labeled as strings: "0", "1", ..., str(num_nodes-1).
    Each possible edge is included with probability edge_prob.
    """
    nodes = [str(i) for i in range(num_nodes)]
    adj = {u: [] for u in nodes}

    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if random.random() < edge_prob:
                u, v = nodes[i], nodes[j]
                adj[u].append(v)
                adj[v].append(u)
    return adj


def save_graph(adj: dict, filename: str):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(adj, f, indent=2)


def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_graphs.py <num_nodes_graph1> <num_nodes_graph2> [edge_prob]")
        print("Example: python generate_graphs.py 5 6 0.4")
        sys.exit(1)

    n1 = int(sys.argv[1])
    n2 = int(sys.argv[2])
    edge_prob = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3

    g1 = generate_random_graph(n1, edge_prob)
    g2 = generate_random_graph(n2, edge_prob)

    save_graph(g1, "sample_graphs/g1.json")
    save_graph(g2, "sample_graphs/g2.json")

    print(f"Generated sample_graphs/g1.json with {n1} nodes, sample_graphs/g2.json with {n2} nodes (edge_prob={edge_prob})")


if __name__ == "__main__":
    main()
