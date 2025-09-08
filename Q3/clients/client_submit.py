import json
import sys
from typing import Dict, List

import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc

from protofiles import graph_service_pb2 as pb
from protofiles import graph_service_pb2_grpc as pb_grpc


def load_adjacency_from_json(path: str) -> Dict[str, List[str]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Expecting: {"A": ["B","C"], "B": ["A"], "C": []}
    return {str(k): [str(x) for x in v] for k, v in data.items()}


def main():
    if len(sys.argv) < 4:
        print("Usage: python clients/client_submit.py <client_id> <adjacency.json> <server_addr host:port>")
        print("Example: python clients/client_submit.py clientA sample_graphs/g1.json localhost:50051")
        sys.exit(1)

    client_id = sys.argv[1]
    json_path = sys.argv[2]
    target = sys.argv[3]

    adj = load_adjacency_from_json(json_path)

    channel = grpc.insecure_channel(target)
    stub = pb_grpc.GraphServiceStub(channel)

    req = pb.SubmitGraphRequest(client_id=client_id)
    for u, nbrs in adj.items():
        req.adjacency[u].neighbors.extend(nbrs)

    resp = stub.SubmitGraph(req)
    print(
        f"Submitted for {client_id}: nodes={resp.client_nodes}, edges={resp.client_edges} | "
        f"UNION: nodes={resp.union_nodes}, edges={resp.union_edges}"
    )


if __name__ == "__main__":
    main()
