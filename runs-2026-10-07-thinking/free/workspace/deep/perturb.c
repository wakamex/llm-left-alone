// Perturbation-theory Mandelbrot deep zoom with rebasing (Zhuoran's method).
// usage: perturb ref.bin outdir N f0 f1 W H ss [probe]
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <complex.h>

static int P; static double complex *Z, K;
static double renorm(double complex dc);

static double pixel(double complex dc, long maxit, long *iters) {
    double complex d = 0;
    long m = 0;
    for (long n = 0; n < maxit; n++) {
        d = (2 * Z[m] + d) * d + dc;
        m++;
        double complex z = Z[m] + d;
        double az = creal(z) * creal(z) + cimag(z) * cimag(z);
        if (az > 1e8) { *iters += n; return n + 1 - log2(0.5 * log(az)); }
        double ad = creal(d) * creal(d) + cimag(d) * cimag(d);
        if (az < ad || m == P) { d = z; m = 0; }       // rebase
    }
    *iters += maxit;
    return renorm(dc);
}

static double RENORM_DELTA = 0; /* set to 3.1 P in main */
static int RENORM_ON = 1;
// Near the final minibrot, every P-th iterate obeys w <- w^2 + c' with c' = dc/K (verified numerically).
static double renorm(double complex dc) {
    if (!RENORM_ON || cabs(dc) > 3 * cabs(K)) return -1;
    double complex cp = dc / K, w = 0;
    for (int j = 0; j < 20000; j++) {
        w = w * w + cp;
        double aw = creal(w) * creal(w) + cimag(w) * cimag(w);
        if (aw > 1e6) return P * (j + 1 - log2(0.5 * log(aw) / log(1e3))) + RENORM_DELTA;
    }
    return -1;
}

static double smoothstep(double x) { x = x < 0 ? 0 : x > 1 ? 1 : x; return x * x * (3 - 2 * x); }

int main(int argc, char **argv) {
    FILE *rf = fopen(argv[1], "rb");
    double kk[2];
    fread(&P, 4, 1, rf); fread(kk, 8, 2, rf); K = kk[0] + I * kk[1];
    Z = malloc((P + 1) * sizeof *Z); fread(Z, sizeof *Z, P + 1, rf); fclose(rf);
    if (argv[2][0] == 't') {   // test mode: perturb ref.bin t off1 off2 ...
        for (int i = 3; i + 1 < argc; i += 2) {
            double complex cp = strtod(argv[i], 0) + I * strtod(argv[i + 1], 0);
            long it = 0; RENORM_ON = 0; double nu = pixel(cp * K, 2000000000L, &it);
            RENORM_ON = 1; double nr = renorm(cp * K);
            printf("c'=%s%+si: perturb nu %.1f   renorm nu %.1f   diff %.1f (%.3f P)\n", argv[i], argv[i+1], nu, nr, nu - nr, (nu - nr) / P); }
        return 0;
    }
    RENORM_DELTA = 3.1 * P;
    const char *dir = argv[2];
    int N = atoi(argv[3]), f0 = atoi(argv[4]), f1 = atoi(argv[5]);
    int W = atoi(argv[6]), H = atoi(argv[7]), ss = atoi(argv[8]);
    int probe = argc > 9;
    double span0 = 3.5, span1 = 3.2 * cabs(K);
    double rot = carg(K);
    float *img = malloc(sizeof(float) * W * H * ss * ss);
    for (int f = f0; f < f1; f++) {
        double t = (double)f / (N - 1);
        double span = span0 * pow(span1 / span0, t);
        double depth = log10(span0 / span);
        // iteration budget: grows with depth, jumps to multiples of P near the minibrots
        double complex u = cexp(I * rot * smoothstep((depth - 30) / 21)) * span;  // rotate to align final minibrot
        // centre offset: drift from main-set centre to nucleus early on
        double complex off = (-0.5 + 0.0 * I) * (1 - smoothstep(depth / 1.0)) ;
        // adaptive budget: low-res preview with a huge cap, take 99.7th pct of escaped counts
        long maxit;
        {
            int pw = 96, ph = 54, n = 0; long cap = 1000 + 12L * P;
            long *v = malloc(sizeof(long) * pw * ph);
            #pragma omp parallel for schedule(dynamic, 1)
            for (int j = 0; j < pw * ph; j++) {
                double fx = (j % pw + 0.5) / pw - 0.5, fy = ((j / pw + 0.5) / ph - 0.5) * H / W;
                long it = 0; double nu = pixel((fx - I * fy) * u + off, cap, &it);
                v[j] = nu < 0 ? -1 : it;
            }
            for (int j = 0; j < pw * ph; j++) if (v[j] >= 0) v[n++] = v[j];
            int cmp(const void *a, const void *b) { long x = *(long *)a, y = *(long *)b; return (x > y) - (x < y); }
            qsort(v, n, sizeof(long), cmp);
            maxit = n ? (long)(1.3 * v[(int)(0.997 * (n - 1))]) + 500 : cap;
            if (maxit > cap) maxit = cap;
            free(v);
        }
        long total = 0; int inside = 0;
        #pragma omp parallel for schedule(dynamic, 1) reduction(+:total, inside)
        for (int py = 0; py < H; py++) {
            long it = 0;
            for (int px = 0; px < W; px++) {
                for (int s = 0; s < ss * ss; s++) {
                    double fx = (px + (s % ss + 0.5) / ss) / W - 0.5;
                    double fy = ((py + (s / ss + 0.5) / ss) / H - 0.5) * H / W;
                    double nu = pixel((fx - I * fy) * u + off, maxit, &it);
                    if (nu < 0) inside++;
                    img[((size_t)py * W + px) * ss * ss + s] = (float)nu;
                }
            }
            total += it;
        }
        if (1) fprintf(stderr, "frame %d depth %.1f maxit %ld avg_iters %.0f inside %.1f%%\n",
                           f, depth, maxit, (double)total / W / H / ss / ss, 100.0 * inside / W / H / ss / ss);
        char fn[256]; snprintf(fn, sizeof fn, "%s/f%04d.nu", dir, f);
        FILE *o = fopen(fn, "wb"); int hdr[3] = {W, H, ss}; fwrite(hdr, 4, 3, o);
        fwrite(img, sizeof(float), (size_t)W * H * ss * ss, o); fclose(o);
    }
    return 0;
}
