#!/usr/bin/env python3
"""
An optimized MPI-based MapReduce framework for counting triangles.

This version implements the 'Orient-by-Degree' algorithm to significantly
reduce intermediate data and avoid redundant counting. It also uses a more
robust shuffle mechanism (Alltoallv) and an object-oriented design.
"""

import sys
import os
import pickle
import time
from collections import defaultdict
from itertools import combinations
from mpi4py import MPI

# ==============================================================================
#  Reusable MPI MapReduce Framework
# ==============================================================================

class MPIBase:
    """A base class that provides the generic framework for an MPI MapReduce job."""
    def __init__(self, comm):
        self.comm = comm
        self.rank = comm.Get_rank()
        self.size = comm.Get_size()

    def _shuffle(self, data_to_send):
        """
        Implements a robust shuffle using a two-phase Alltoallv.
        This handles variable-sized data buckets efficiently.
        """
        # 1. Serialize local data buckets using pickle for efficient network transfer.
        send_data_pickled = [pickle.dumps(bucket) for bucket in data_to_send]
        send_counts = [len(p) for p in send_data_pickled]

        # 2. Exchange the sizes of the data chunks first.
        recv_counts = self.comm.alltoall(send_counts)

        # 3. Prepare send/receive buffers for the actual data exchange.
        sdispls = [0] * self.size
        offset = 0
        for i, p_data in enumerate(send_data_pickled):
            sdispls[i] = offset
            offset += len(p_data)
        send_buf = b''.join(send_data_pickled)

        rdispls = [0] * self.size
        recv_buf_size = sum(recv_counts)
        recv_buf = bytearray(recv_buf_size)
        offset = 0
        for i, count in enumerate(recv_counts):
            rdispls[i] = offset
            offset += count

        # 4. Perform the variable-sized all-to-all communication.
        self.comm.Alltoallv([send_buf, send_counts, sdispls, MPI.BYTE],
                            [recv_buf, recv_counts, rdispls, MPI.BYTE])

        # 5. Deserialize the received data buckets.
        received_buckets = []
        for i in range(self.size):
            if recv_counts[i] > 0:
                start = rdispls[i]
                end = start + recv_counts[i]
                bucket = pickle.loads(recv_buf[start:end])
                received_buckets.append(bucket)
        
        return received_buckets

    def run_job(self, data):
        """Orchestrates a single, complete MapReduce job."""
        # Step 1: Scatter initial data from root to all processes.
        if self.rank == 0:
            chunks = [[] for _ in range(self.size)]
            for i, item in enumerate(data):
                chunks[i % self.size].append(item)
        else:
            chunks = None
        local_data = self.comm.scatter(chunks, root=0)

        # Step 2: MAP PHASE - Each process runs the mapper on its local data.
        map_output = []
        for item in local_data:
            map_output.extend(self.mapper(item))

        # Step 3: SHUFFLE PHASE - Distribute map output to reducer processes.
        send_buckets = [[] for _ in range(self.size)]
        for key, value in map_output:
            target_rank = hash(key) % self.size
            send_buckets[target_rank].append((key, value))
        
        received_buckets = self._shuffle(send_buckets)

        # Step 4: REDUCE PHASE - Group by key and run the reducer.
        grouped_data = defaultdict(list)
        for bucket in received_buckets:
            for key, value in bucket:
                grouped_data[key].append(value)
        
        reduce_output = []
        for key, values in grouped_data.items():
            reduce_output.extend(self.reducer(key, values))

        # Step 5: Gather final results from all processes to the root.
        all_results = self.comm.gather(reduce_output, root=0)

        if self.rank == 0:
            final_result = []
            if all_results:
                for res_list in all_results:
                    if res_list:
                        final_result.extend(res_list)
            return final_result
        return None

# ==============================================================================
#  Specific Triangle Counting Jobs
# ==============================================================================

class DegreeCounter(MPIBase):
    """Job 1: Calculates the degree of each vertex."""
    def mapper(self, line):
        if not line.strip(): return []
        u, v = map(int, line.strip().split())
        yield u, 1
        yield v, 1
    def reducer(self, key, values):
        yield key, sum(values)

class AdjListBuilder(MPIBase):
    """Job 2: Builds an oriented (directed) adjacency list."""
    def __init__(self, comm, degrees):
        super().__init__(comm)
        self.degrees = degrees
    def mapper(self, line):
        if not line.strip(): return []
        u, v = map(int, line.strip().split())
        deg_u, deg_v = self.degrees.get(u, 0), self.degrees.get(v, 0)
        # Create a directed edge from lower-degree to higher-degree node.
        # This is the core of the 'orient-by-degree' optimization.
        if deg_u < deg_v or (deg_u == deg_v and u < v):
            yield u, v
        else:
            yield v, u
    def reducer(self, key, values):
        yield key, sorted(list(values))

class WedgeAndEdgeEmitter(MPIBase):
    """Job 3: Emits wedges and the edges that could close them."""
    def mapper(self, item):
        u, neighbors = item
        # Emit edges from the oriented graph.
        for v in neighbors:
            # Key is the edge tuple, sorted to be canonical.
            yield tuple(sorted((u, v))), ('edge',)
        
        # Emit wedges. A wedge u -> (v, w) means we need to check for edge (v, w).
        if len(neighbors) > 1:
            for v, w in combinations(neighbors, 2):
                # Key is the potential closing edge. Value is the wedge center.
                yield tuple(sorted((v, w))), ('wedge', u)
    def reducer(self, key, values):
        # Pass through all wedges and edges for the final counting job.
        for v in values:
            yield key, v

class TriangleCounter(MPIBase):
    """Job 4: Joins wedges and edges to find and count triangles."""
    def reducer(self, key, values):
        wedges = []
        edge_exists = False
        # For a given key (potential closing edge), check if we received both
        # an 'edge' type and one or more 'wedge' types.
        for v_type, *v_data in values:
            if v_type == 'edge':
                edge_exists = True
            elif v_type == 'wedge':
                wedges.append(v_data[0])
        
        # If the closing edge exists, every wedge is a confirmed triangle.
        if edge_exists and wedges:
            v, w = key
            for u in wedges:
                # Emit a count of 1 for each vertex in the triangle.
                yield u, 1
                yield v, 1
                yield w, 1
    def mapper(self, item): # Mapper is just a pass-through
        yield item

class CountAggregator(MPIBase):
    """Job 5: A final aggregation to sum the per-vertex counts."""
    def mapper(self, item):
        yield item
    def reducer(self, key, values):
        yield key, sum(values)

# ==============================================================================
#  Main Driver
# ==============================================================================

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    
    start_time = 0.0
    if rank == 0:
        if len(sys.argv) < 2:
            print("Usage: python mpi_mapreduce_optimized.py <input_file>", file=sys.stderr)
            comm.Abort()
        
        print(f"--- Starting Optimized MPI Triangle Counting Job with {comm.Get_size()} processes ---")
        start_time = time.time()

    input_file = sys.argv[1]
    lines = None
    if rank == 0:
        try:
            with open(input_file, 'r') as f: lines = f.readlines()
        except FileNotFoundError:
            print(f"Error: Input file '{input_file}' not found.", file=sys.stderr)
            lines = "ERROR" # Signal error
    
    lines = comm.bcast(lines, root=0)
    if lines == "ERROR":
        comm.Abort()

    # --- Job 1: Calculate node degrees ---
    degrees = dict(DegreeCounter(comm).run_job(lines) or [])
    degrees = comm.bcast(degrees, root=0)

    # --- Job 2: Build oriented adjacency lists ---
    adj_lists = AdjListBuilder(comm, degrees).run_job(lines)

    # --- Job 3: Generate Wedges and Edges ---
    wedges_and_edges = WedgeAndEdgeEmitter(comm).run_job(adj_lists)
    
    # --- Job 4: Count Triangles by closing wedges ---
    per_vertex_ones = TriangleCounter(comm).run_job(wedges_and_edges)

    # --- Job 5: Aggregate per-vertex counts ---
    per_vertex_counts = CountAggregator(comm).run_job(per_vertex_ones)

    end_time = time.time()
    # --- Final Output ---
    if rank == 0:
        total_triangles = 0
        if per_vertex_counts:
            # Because we find each triangle exactly once, the sum of per-vertex
            # counts will be 3 * total_triangles.
            total_triangles = sum(count for _, count in per_vertex_counts) // 3
        
        with open("global_counts.txt", "w") as f:
            f.write(f"total_triangles\t{total_triangles}\n")
            
        with open("per_vertex_counts.txt", "w") as f:
            if per_vertex_counts:
                for vertex, count in sorted(per_vertex_counts):
                    f.write(f"{vertex}\t{count}\n")
        print(f"Total triangles found: {total_triangles}")

        print(f"Total execution time: {end_time - start_time:.4f} seconds.")

if __name__ == '__main__':
    main()
