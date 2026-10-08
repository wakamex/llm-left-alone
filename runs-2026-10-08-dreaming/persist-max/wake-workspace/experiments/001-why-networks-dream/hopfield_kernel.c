/*
 * Asynchronous Hopfield dynamics, run until nothing changes.
 *
 *   W : N*N symmetric weights, row-major, zero diagonal
 *   s : N states in {-1,+1}, updated in place
 *   seed : seeds the random update order (xorshift64*)
 *
 * Returns the number of sweeps it took to settle, or -1 if it didn't settle
 * within max_sweeps. Local fields are recomputed from scratch every sweep so
 * floating-point drift can't build up.
 *
 * Build: cc -O2 -shared -fPIC -o hopfield_kernel.so hopfield_kernel.c
 */
#include <stdint.h>
#include <stdlib.h>

static uint64_t next_u64(uint64_t *x) {
    *x ^= *x >> 12;
    *x ^= *x << 25;
    *x ^= *x >> 27;
    return *x * 2685821657736338717ULL;
}

int settle(const double *W, int N, signed char *s, uint64_t seed, int max_sweeps) {
    double *h = malloc(sizeof(double) * (size_t)N);
    int *perm = malloc(sizeof(int) * (size_t)N);
    uint64_t rng = seed ? seed : 0x9E3779B97F4A7C15ULL;
    int result = -1;
    if (!h || !perm) goto done;
    for (int i = 0; i < N; i++) perm[i] = i;

    for (int sweep = 0; sweep < max_sweeps; sweep++) {
        for (int i = 0; i < N; i++) {
            const double *row = W + (size_t)i * N;
            double acc = 0.0;
            for (int j = 0; j < N; j++) acc += row[j] * s[j];
            h[i] = acc;
        }
        for (int k = N - 1; k > 0; k--) {
            int j = (int)(next_u64(&rng) % (uint64_t)(k + 1));
            int t = perm[k]; perm[k] = perm[j]; perm[j] = t;
        }
        int flips = 0;
        for (int k = 0; k < N; k++) {
            int i = perm[k];
            signed char v = h[i] > 0.0 ? 1 : (h[i] < 0.0 ? -1 : s[i]);
            if (v != s[i]) {
                const double *row = W + (size_t)i * N; /* symmetric: column i == row i */
                double d = 2.0 * v;
                for (int j = 0; j < N; j++) h[j] += d * row[j];
                s[i] = v;
                flips++;
            }
        }
        if (flips == 0) { result = sweep + 1; break; }
    }
done:
    free(h);
    free(perm);
    return result;
}
