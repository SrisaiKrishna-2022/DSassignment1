import threading
from concurrent import futures
import networkx as nx
from networkx.algorithms.clique import graph_clique_number

import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc

from protofiles import graph_service_pb2 as pb
from protofiles import graph_service_pb2_grpc as pb_grpc


class GraphStore:
    """
    Thread-safe store of per-client graphs and operations on their union.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self._client_graphs = {}  # client_id -> nx.Graph

    def reset(self):
        with self._lock:
            self._client_graphs.clear()

    def set_client_graph(self, client_id: str, g: nx.Graph):
        with self._lock:
            self._client_graphs[client_id] = g.copy()

    def union_graph(self) -> nx.Graph:
        with self._lock:
            if not self._client_graphs:
                return nx.Graph()
            # Compose all graphs (union of nodes/edges).
            graphs = list(self._client_graphs.values())
            return nx.compose_all(graphs)

    def stats(self):
        ug = self.union_graph()
        return ug.number_of_nodes(), ug.number_of_edges()


def adjacency_map_to_graph(adjacency_map) -> nx.Graph:
    """
    Convert the protobuf map<string, NodeList> into an undirected NetworkX Graph.
    We make edges undirected; self-loops are ignored; duplicate edges are fine.
    """
    G = nx.Graph()
    # Ensure all nodes appear even if they have no neighbors.
    for u in adjacency_map:
        G.add_node(u)

    for u, node_list in adjacency_map.items():
        for v in node_list.neighbors:
            if u == v:
                continue  # ignore self-loops
            G.add_edge(u, v)
    return G


class GraphService(pb_grpc.GraphServiceServicer):
    def __init__(self, store: GraphStore):
        self.store = store

    def SubmitGraph(self, request: pb.SubmitGraphRequest, context):
        client_id = request.client_id.strip()
        if not client_id:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "client_id must be non-empty")

        G = adjacency_map_to_graph(request.adjacency)

        self.store.set_client_graph(client_id, G)
        union_nodes, union_edges = self.store.stats()

        return pb.SubmitGraphResponse(
            client_nodes=G.number_of_nodes(),
            client_edges=G.number_of_edges(),
            union_nodes=union_nodes,
            union_edges=union_edges,
        )

    def HasIndependentSet(self, request: pb.QueryK, context):
        k = request.k
        if k < 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "k must be >= 0")

        UG = self.store.union_graph()

        if k == 0:
            return pb.BoolReply(ok=True)
        if UG.number_of_nodes() < k:
            return pb.BoolReply(ok=False)

        comp = nx.complement(UG)
        try:
            clique_num = graph_clique_number(comp)
        except Exception:
            clique_num = 0

        return pb.BoolReply(ok=(clique_num >= k))

    def HasMatching(self, request: pb.QueryK, context):
        k = request.k
        if k < 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "k must be >= 0")

        UG = self.store.union_graph()
        if k == 0:
            return pb.BoolReply(ok=True)
        if UG.number_of_edges() == 0:
            return pb.BoolReply(ok=False)

        # EXACT maximum matching in general graphs (Edmonds/Blossom).
        matching = nx.algorithms.matching.max_weight_matching(UG, maxcardinality=True)
        # matching is a set of frozenset({u, v}); its size is the number of edges in the matching
        size = len(matching)
        return pb.BoolReply(ok=(size >= k))

    def Reset(self, request: pb.ResetRequest, context):
        self.store.reset()
        return pb.ResetResponse(cleared=True)


def serve(host="0.0.0.0", port=50051, max_workers=8):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    store = GraphStore()
    pb_grpc.add_GraphServiceServicer_to_server(GraphService(store), server)
    server.add_insecure_port(f"{host}:{port}")
    server.start()
    print(f"[gRPC] GraphService listening on {host}:{port}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
