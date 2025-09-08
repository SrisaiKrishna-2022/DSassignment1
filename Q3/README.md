# Q3: Distributed Graph Queries with gRPC

This project implements a gRPC server that merges graphs from multiple clients and answers graph property queries.  
The system supports asynchronous graph submissions and provides query results on the **combined graph**.

---

## 📌 Features
- Clients submit graphs (in adjacency list JSON format).
- Server merges graphs asynchronously.
- Queries supported:
  - `HasIndependentSet(k)` → True if combined graph has an independent set of size ≥ k.
  - `HasMatching(k)` → True if combined graph has a matching of size ≥ k.
- End-to-end tested with sample graph datasets.

---

## ⚙️ How to Run

1. **Generate Graphs**
- In Q3 path, run
    ```
    python generate_graphs.py x y
    ```
    ***Note:*** where x, y are the sizes of the graphs

2. **Generate gRPC Files**
- Run this protofiles path
    ```
    python -m grpc_tools.protoc -I../protofiles/ --python_out=. --pyi_out=. --grpc_python_out=. graph_service.proto
    ```

    ***Note:***  After the new files are generated, then change the "graph_service_pb2" to "protofiles.graph_service_pb2" in "graph_service_pb2_grpc.py" file

3. **Start Server**
- Then Run,
    ```
    python3 server.py
    ```
4. **Run Clients**
- Then Run these four commands(in-order) in Q3 path 
    ```
    python clients/client_submit.py clientA sample_graphs/g1.json localhost:50051
    ```
    ```
    python clients/client_submit.py clientB sample_graphs/g2.json localhost:50051
    ```
    ```
    python clients/client_query.py localhost:50051 indep 3
    ```
    ```
    python clients/client_query.py localhost:50051 match 2
    ```