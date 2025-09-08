#include <bits/stdc++.h>
#include <mpi.h>
using namespace std;

using SparseRow = vector<pair<int, double>>;
using SparseMatrix = vector<SparseRow>;

void print_sparse_matrix(SparseMatrix& matrix) {
    for (auto& row : matrix) {
        cout << row.size();
        for ( auto& elem : row) {
            cout << " " << elem.first << " " << elem.second;
        }
        cout << endl;
    }
}

vector<double> serialize_matrix_chunk(SparseMatrix& matrix_chunk) {
    vector<double> buffer;
    buffer.push_back(matrix_chunk.size()); 

    for (auto& row : matrix_chunk) {
        buffer.push_back(row.size()); 
        for ( auto& elem : row) {
            buffer.push_back(elem.first);
            buffer.push_back(elem.second);
        }
    }
    return buffer;
}

SparseMatrix deserialize_matrix_chunk( vector<double>& buffer) {
    SparseMatrix matrix_chunk;
    if (buffer.empty()) return matrix_chunk;

    int buffer_idx = 0;
    int num_rows = buffer[buffer_idx++];
    matrix_chunk.resize(num_rows);

    for (int i = 0; i < num_rows; ++i) {
        int k = buffer[buffer_idx++];
        for (int j = 0; j < k; ++j) {
            int col = buffer[buffer_idx++];
            double val = buffer[buffer_idx++];
            matrix_chunk[i].push_back({col, val});
        }
    }
    return matrix_chunk;
}


int main(int argc, char* argv[]) {
    MPI_Init(&argc, &argv);

    int world_rank, world_size;
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);

    int N, M, P;
    SparseMatrix A, B, B_T;
    double start_time, end_time;

    // =================================================================
    // Phase 1: Root process reads data and prepares for distribution
    // =================================================================
    if (world_rank == 0) {
        cin >> N >> M >> P;
        start_time= MPI_Wtime();
        
        A.resize(N);
        string line;
        getline(cin, line); // Consume the rest of the first line

        // Read Matrix A
        for (int i = 0; i < N; ++i) {
            getline(cin, line);
            stringstream ss(line);
            int k;
            ss >> k;
            for (int j = 0; j < k; ++j) {
                int col;
                double val;
                ss >> col >> val;
                A[i].push_back({col, val});
            }
        }

        // Read Matrix B
        B.resize(M);
        for (int i = 0; i < M; ++i) {
            getline(cin, line);
            stringstream ss(line);
            int k;
            ss >> k;
            for (int j = 0; j < k; ++j) {
                int col;
                double val;
                ss >> col >> val;
                B[i].push_back({col, val});
            }
        }

        // Transpose Matrix B to get B_T
        B_T.resize(P);
        for (int i = 0; i < M; ++i) {
            for ( auto& elem : B[i]) {
                B_T[elem.first].push_back({i, elem.second});
            }
        }
    }

    // =================================================================
    // Phase 2: Broadcast essential information to all processes
    // =================================================================
    MPI_Bcast(&N, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&M, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&P, 1, MPI_INT, 0, MPI_COMM_WORLD);

    // Serialize and broadcast the transposed matrix B_T
    vector<double> b_t_buffer;
    if (world_rank == 0) {
        b_t_buffer = serialize_matrix_chunk(B_T);
    }
    
    int b_t_buffer_size;
    if (world_rank == 0) {
        b_t_buffer_size = b_t_buffer.size();
    }
    MPI_Bcast(&b_t_buffer_size, 1, MPI_INT, 0, MPI_COMM_WORLD);

    if (world_rank != 0) {
        b_t_buffer.resize(b_t_buffer_size);
    }
    MPI_Bcast(b_t_buffer.data(), b_t_buffer_size, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    
    // All processes deserialize B_T from the buffer
    if (world_rank != 0) {
         B_T = deserialize_matrix_chunk(b_t_buffer);
    }


    // =================================================================
    // Phase 3: Scatter rows of A from root to all processes
    // =================================================================
    SparseMatrix A_chunk;
    int rows_per_proc = N / world_size;
    int extra_rows = N % world_size;

    if (world_rank == 0) {
        int current_row = 0;
        for (int i = 0; i < world_size; ++i) {
            int chunk_size = rows_per_proc + (i < extra_rows ? 1 : 0);
            if (i == 0) { // Root's own chunk
                 A_chunk.assign(A.begin() + current_row, A.begin() + current_row + chunk_size);
            } else {
                SparseMatrix temp_chunk(A.begin() + current_row, A.begin() + current_row + chunk_size);
                vector<double> a_chunk_buffer = serialize_matrix_chunk(temp_chunk);
                int buffer_size = a_chunk_buffer.size();
                MPI_Send(&buffer_size, 1, MPI_INT, i, 0, MPI_COMM_WORLD);
                MPI_Send(a_chunk_buffer.data(), buffer_size, MPI_DOUBLE, i, 1, MPI_COMM_WORLD);
            }
            current_row += chunk_size;
        }
    } else {
        int buffer_size;
        MPI_Recv(&buffer_size, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        vector<double> a_chunk_buffer(buffer_size);
        MPI_Recv(a_chunk_buffer.data(), buffer_size, MPI_DOUBLE, 0, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        A_chunk = deserialize_matrix_chunk(a_chunk_buffer);
    }

    // =================================================================
    // Phase 4: Parallel Computation
    // =================================================================
    SparseMatrix C_chunk;
    C_chunk.resize(A_chunk.size());

    for (int i = 0; i < A_chunk.size(); ++i) {
        map<int, double> a_row_map(A_chunk[i].begin(), A_chunk[i].end());
        for (int j = 0; j < P; ++j) {
            // Compute dot product of A_chunk[i] and B_T[j]
            double sum = 0.0;
            // Use a map for efficient lookup in the smaller row
            for( auto& b_elem : B_T[j]) {
                auto it = a_row_map.find(b_elem.first); // b_elem.first is the column index in A
                if (it != a_row_map.end()) {
                    sum += it->second * b_elem.second;
                }
            }
            if (sum != 0.0) {
                C_chunk[i].push_back({j, sum});
            }
        }
    }

    // =================================================================
    // Phase 5: Gather results back to the root process
    // =================================================================
    if (world_rank != 0) {
        vector<double> c_chunk_buffer = serialize_matrix_chunk(C_chunk);
        int buffer_size = c_chunk_buffer.size();
        MPI_Send(&buffer_size, 1, MPI_INT, 0, 2, MPI_COMM_WORLD);
        MPI_Send(c_chunk_buffer.data(), buffer_size, MPI_DOUBLE, 0, 3, MPI_COMM_WORLD);
    } else {
        SparseMatrix C(N);
        int current_row = 0;

        // Place root's own results
        for( auto& row : C_chunk) {
            C[current_row++] = row;
        }

        // Receive results from other processes
        for (int i = 1; i < world_size; ++i) {
            int buffer_size;
            MPI_Recv(&buffer_size, 1, MPI_INT, i, 2, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            vector<double> c_chunk_buffer(buffer_size);
            MPI_Recv(c_chunk_buffer.data(), buffer_size, MPI_DOUBLE, i, 3, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            
            SparseMatrix received_chunk = deserialize_matrix_chunk(c_chunk_buffer);
            for( auto& row : received_chunk) {
                C[current_row++] = row;
            }
        }
        
        // =================================================================
        // Phase 6: Root prints the final result
        // =================================================================
        end_time = MPI_Wtime();
        // print_sparse_matrix(C);
        fprintf(stderr, "TIME_TAKEN,%d,%.6f\n", world_size, end_time - start_time);
    }

    MPI_Finalize();
    return 0;
}