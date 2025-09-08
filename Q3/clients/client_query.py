import sys
import grpc

import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protofiles import graph_service_pb2 as pb
from protofiles import graph_service_pb2_grpc as pb_grpc

def main():
    if len(sys.argv) < 4:
        print("Usage: python clients/client_query.py <server_addr host:port> <indep|match> <k>")
        print("Example: python clients/client_query.py localhost:50051 indep 4")
        print("         python clients/client_query.py localhost:50051 match 3")
        sys.exit(1)

    target = sys.argv[1]
    qtype = sys.argv[2].lower()
    k = int(sys.argv[3])

    channel = grpc.insecure_channel(target)
    stub = pb_grpc.GraphServiceStub(channel)

    if qtype in ("indep", "independent", "independentset"):
        ans = stub.HasIndependentSet(pb.QueryK(k=k))
        print(f"HasIndependentSet(k={k}) -> {ans.ok}")
    elif qtype in ("match", "matching"):
        ans = stub.HasMatching(pb.QueryK(k=k))
        print(f"HasMatching(k={k}) -> {ans.ok}")
    else:
        print("Unknown query type. Use 'indep' or 'match'.")
        sys.exit(2)


if __name__ == "__main__":
    main()
