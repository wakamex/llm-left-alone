// Deep zoom: perturbation + rebasing + bilinear approximation (BLA) + minibrot renormalization.
// usage: bla ref.bin outdir N f0 f1 W H ss          render frames (raw float nu)
//        bla ref.bin t eps re im [re im ...]          compare BLA vs plain perturbation at c = c0 + c'K
#include <complex.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef double complex cplx;
static int P; static cplx *Z, K;
static double EPS = 1e-12, RENORM_DELTA;

typedef struct { cplx A, B; double R; } Bla;
static Bla *lv[32]; static int nlv;          // lv[l][k] covers steps m = 1 + k*2^l .. +2^l

static double n2(cplx z) { return creal(z) * creal(z) + cimag(z) * cimag(z); }

static void build_bla(double dcmax) {
    for (int l = 0; l < nlv; l++) free(lv[l]);
    int n = P - 1;                                    // steps m = 1 .. P-1
    lv[0] = malloc(sizeof(Bla) * n);
    for (int k = 0; k < n; k++) {
        cplx z = Z[1 + k];
        lv[0][k] = (Bla){2 * z, 1, EPS * cabs(z)};
    }
    nlv = 1;
    while (n > 1) {
        int m = n / 2;
        Bla *a = lv[nlv - 1], *b = malloc(sizeof(Bla) * m);
        for (int k = 0; k < m; k++) {
            Bla x = a[2 * k], y = a[2 * k + 1];
            double r2 = (y.R - cabs(x.B) * dcmax) / cabs(x.A);
            b[k] = (Bla){y.A * x.A, y.A * x.B + y.B, fmin(x.R, r2 > 0 ? r2 : 0)};
        }
        lv[nlv++] = b; n = m;
    }
}

static double renorm(cplx dc) {
    if (cabs(dc) > 3 * cabs(K)) return -1;
    cplx cp = dc / K, w = 0;
    for (int j = 0; j < 20000; j++) {
        w = w * w + cp;
        double aw = n2(w);
        if (aw > 1e6) return (double)P * (j + 1 - log2(0.5 * log(aw) / log(1e3))) + RENORM_DELTA;
    }
    return -1;
}

static double pixel(cplx dc, long maxit, int use_bla, int use_renorm, long *iters) {
    cplx d = 0; long m = 0, n = 0;
    while (n < maxit) {
        if (m > 0 && use_bla) {                       // try the biggest valid skip
            double ad = cabs(d);
            long off = m - 1; int done = 0;
            for (int l = nlv - 1; l >= 0 && !done; l--) {
                long step = 1L << l;
                if (off % step) continue;
                long k = off >> l;
                if (m + step > P || ad >= lv[l][k].R || n + step > maxit) continue;
                if ((k << l) + step > P - 1) continue;
                Bla *b = &lv[l][k];
                d = b->A * d + b->B * dc; m += step; n += step; done = 1;
            }
            if (!done) { d = (2 * Z[m] + d) * d + dc; m++; n++; }
        } else { d = (2 * Z[m] + d) * d + dc; m++; n++; }
        cplx z = Z[m] + d;
        double az = n2(z);
        if (az > 1e8) { *iters += n; return n - log2(0.5 * log(az)); }
        if (az < n2(d) || m == P) { d = z; m = 0; }   // rebase
    }
    *iters += maxit;
    return use_renorm ? renorm(dc) : -1;
}

static double smoothstep(double x) { x = x < 0 ? 0 : x > 1 ? 1 : x; return x * x * (3 - 2 * x); }

int main(int argc, char **argv) {
    FILE *rf = fopen(argv[1], "rb"); double kk[2];
    if (fread(&P, 4, 1, rf) != 1 || fread(kk, 8, 2, rf) != 2) return 1;
    K = kk[0] + I * kk[1];
    Z = malloc((P + 1) * sizeof *Z);
    if (fread(Z, sizeof *Z, P + 1, rf) != (size_t)P + 1) return 1;
    fclose(rf);
    RENORM_DELTA = 3.1 * P;
    if (argv[2][0] == 't') {
        EPS = atof(argv[3]);
        for (int i = 4; i + 1 < argc; i += 2) {
            cplx cp = atof(argv[i]) + I * atof(argv[i + 1]), dc = cp * K;
            build_bla(cabs(dc));
            long i1 = 0, i2 = 0; struct timespec t0, t1, t2;
            clock_gettime(CLOCK_MONOTONIC, &t0); double a = pixel(dc, 4000000000L, 0, 0, &i1);
            clock_gettime(CLOCK_MONOTONIC, &t1); double b = pixel(dc, 4000000000L, 1, 0, &i2);
            clock_gettime(CLOCK_MONOTONIC, &t2);
            double ta = (t1.tv_sec - t0.tv_sec) + 1e-9 * (t1.tv_nsec - t0.tv_nsec);
            double tb = (t2.tv_sec - t1.tv_sec) + 1e-9 * (t2.tv_nsec - t1.tv_nsec);
            printf("c'=(%s,%s) plain %.3f  bla %.3f  diff %.2e   time %.4fs -> %.5fs (x%.0f)\n",
                   argv[i], argv[i + 1], a, b, b - a, ta, tb, ta / tb);
        }
        return 0;
    }
    const char *dir = argv[2];
    int N = atoi(argv[3]), f0 = atoi(argv[4]), f1 = atoi(argv[5]);
    int W = atoi(argv[6]), H = atoi(argv[7]), ss = atoi(argv[8]);
    double span0 = 3.5, span1 = 3.2 * cabs(K), rot = carg(K), dfinal = log10(span0 / span1);
    float *img = malloc(sizeof(float) * W * H * ss * ss);
    for (int f = f0; f < f1; f++) {
        double t = (double)f / (N - 1), span = span0 * pow(span1 / span0, t), depth = log10(span0 / span);
        cplx u = cexp(I * rot * smoothstep((depth - (dfinal - 20)) / 20)) * span;
        cplx off = -0.5 * (1 - smoothstep(depth));
        build_bla(cabs(off) + span * 0.6);
        long maxit;                                    // adaptive budget from a low-res preview
        {
            int pw = 96, ph = 54, n = 0; long cap = 1000 + 12L * P;
            long *v = malloc(sizeof(long) * pw * ph);
            #pragma omp parallel for schedule(dynamic, 1)
            for (int j = 0; j < pw * ph; j++) {
                double fx = (j % pw + 0.5) / pw - 0.5, fy = ((j / pw + 0.5) / ph - 0.5) * H / W;
                long it = 0; double nu = pixel((fx - I * fy) * u + off, cap, 1, 0, &it);
                v[j] = nu < 0 ? -1 : it;
            }
            for (int j = 0; j < pw * ph; j++) if (v[j] >= 0) v[n++] = v[j];
            int cmp(const void *a, const void *b) { long x = *(long *)a, y = *(long *)b; return (x > y) - (x < y); }
            qsort(v, n, sizeof(long), cmp);
            maxit = n ? (long)(1.3 * v[(int)(0.997 * (n - 1))]) + 500 : cap;
            if (maxit > cap) maxit = cap;
            free(v);
        }
        long total = 0; long inside = 0;
        #pragma omp parallel for schedule(dynamic, 1) reduction(+:total, inside)
        for (int py = 0; py < H; py++) {
            long it = 0;
            for (int px = 0; px < W; px++)
                for (int s = 0; s < ss * ss; s++) {
                    double fx = (px + (s % ss + 0.5) / ss) / W - 0.5;
                    double fy = ((py + (s / ss + 0.5) / ss) / H - 0.5) * H / W;
                    double nu = pixel((fx - I * fy) * u + off, maxit, 1, 1, &it);
                    if (nu < 0) inside++;
                    img[((size_t)py * W + px) * ss * ss + s] = (float)nu;
                }
            total += it;
        }
        fprintf(stderr, "frame %d depth %.1f maxit %ld avg_iters %.0f inside %.1f%%\n", f, depth, maxit,
                (double)total / W / H / ss / ss, 100.0 * inside / W / H / ss / ss);
        char fn[256]; snprintf(fn, sizeof fn, "%s/f%04d.nu", dir, f);
        FILE *o = fopen(fn, "wb"); int hdr[3] = {W, H, ss}; fwrite(hdr, 4, 3, o);
        fwrite(img, sizeof(float), (size_t)W * H * ss * ss, o); fclose(o);
    }
    return 0;
}
