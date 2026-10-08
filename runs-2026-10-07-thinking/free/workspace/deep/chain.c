// Minibrot chain search with GMP mpf (same algorithm as chain.py, much faster).
// usage: chain <levels> <bits>   -> prints period, cx, cy, kx, ky
#include <gmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

typedef struct { mpf_t r, i; } C;
static mpf_t t1, t2, t3;
static void cinit(C *a) { mpf_init(a->r); mpf_init(a->i); }
static void cset(C *a, const C *b) { mpf_set(a->r, b->r); mpf_set(a->i, b->i); }
static void cmul(C *o, const C *a, const C *b) {          // o may alias a/b
    mpf_mul(t1, a->r, b->r); mpf_mul(t2, a->i, b->i); mpf_sub(t3, t1, t2);
    mpf_mul(t1, a->r, b->i); mpf_mul(t2, a->i, b->r); mpf_add(o->i, t1, t2); mpf_set(o->r, t3);
}
static void cdiv(C *o, const C *a, const C *b) {
    mpf_t d, x, y; mpf_inits(d, x, y, NULL);
    mpf_mul(t1, b->r, b->r); mpf_mul(t2, b->i, b->i); mpf_add(d, t1, t2);
    mpf_mul(t1, a->r, b->r); mpf_mul(t2, a->i, b->i); mpf_add(x, t1, t2);
    mpf_mul(t1, a->i, b->r); mpf_mul(t2, a->r, b->i); mpf_sub(y, t1, t2);
    mpf_div(o->r, x, d); mpf_div(o->i, y, d); mpf_clears(d, x, y, NULL);
}
static double cabs2d(const C *a) { double x = mpf_get_d(a->r), y = mpf_get_d(a->i); return x * x + y * y; }
// log10 |a| robust for tiny numbers
static double clog10(const C *a) {
    long ex, ey; double x = mpf_get_d_2exp(&ex, a->r), y = mpf_get_d_2exp(&ey, a->i);
    long e = ex > ey ? ex : ey; x = ldexp(x, ex - e); y = ldexp(y, ey - e);
    return (log10(sqrt(x * x + y * y)) + e * log10(2.0));
}

// step: z = z^2 + c, dz = 2 z dz + 1
static C z, dz, tmp;
static void step(const C *c) {
    cmul(&tmp, &z, &dz); mpf_mul_2exp(dz.r, tmp.r, 1); mpf_mul_2exp(dz.i, tmp.i, 1); mpf_add_ui(dz.r, dz.r, 1);
    cmul(&z, &z, &z); mpf_add(z.r, z.r, c->r); mpf_add(z.i, z.i, c->i);
}

// returns period or -1 (escaped); log10r = log10 of ball radius
static long ball_period(const C *c, double log10r, long maxn) {
    mpf_set_ui(z.r, 0); mpf_set_ui(z.i, 0); mpf_set_ui(dz.r, 0); mpf_set_ui(dz.i, 0);
    for (long n = 1; n <= maxn; n++) {
        step(c);
        if (cabs2d(&z) > 1e6) return -n;
        if (clog10(&z) < log10r + clog10(&dz)) return n;
    }
    return 0;
}

int main(int argc, char **argv) {
    int levels = atoi(argv[1]); mp_bitcnt_t bits = atol(argv[2]);
    mpf_set_default_prec(bits); mpf_inits(t1, t2, t3, NULL);
    cinit(&z); cinit(&dz); cinit(&tmp);
    C P0, c, k, o, s, l, b, w; cinit(&P0); cinit(&c); cinit(&k); cinit(&o); cinit(&s); cinit(&l); cinit(&b); cinit(&w);
    mpf_set_str(P0.r, "-0.743643887037151", 10); mpf_set_str(P0.i, "0.131825904205330", 10);
    mpf_set_ui(c.r, 0); mpf_set_ui(c.i, 0); mpf_set_ui(k.r, 1); mpf_set_ui(k.i, 0);
    long period = 0;
    for (int lev = 0; lev < levels; lev++) {
        cmul(&o, &k, &P0); C tg; cinit(&tg); mpf_add(tg.r, c.r, o.r); mpf_add(tg.i, c.i, o.i);
        double lk = clog10(&k);
        period = 0;
        for (int e = 14; e >= 4; e -= 2) {
            long p = ball_period(&tg, lk - e, 50000000);
            fprintf(stderr, "  level %d try r=|K|e-%d -> %ld\n", lev + 1, e, p);
            if (p > 0) { period = p; break; }
        }
        if (!period) { fprintf(stderr, "failed\n"); return 1; }
        cset(&c, &tg);
        for (int it = 0; it < 60; it++) {                       // Newton
            mpf_set_ui(z.r, 0); mpf_set_ui(z.i, 0); mpf_set_ui(dz.r, 0); mpf_set_ui(dz.i, 0);
            for (long n = 0; n < period; n++) step(&c);
            cdiv(&s, &z, &dz); mpf_sub(c.r, c.r, s.r); mpf_sub(c.i, c.i, s.i);
            double ls = clog10(&s);
            if (ls < -(double)bits * 0.30103 + 20 || (mpf_sgn(s.r) == 0 && mpf_sgn(s.i) == 0)) break;
        }
        // size estimate: b = 1 + sum 1/l_j, size = 1/(b l^2)
        mpf_set_ui(z.r, 0); mpf_set_ui(z.i, 0); mpf_set_ui(l.r, 1); mpf_set_ui(l.i, 0);
        mpf_set_ui(b.r, 1); mpf_set_ui(b.i, 0);
        C one; cinit(&one); mpf_set_ui(one.r, 1); mpf_set_ui(one.i, 0);
        for (long j = 1; j < period; j++) {
            cmul(&z, &z, &z); mpf_add(z.r, z.r, c.r); mpf_add(z.i, z.i, c.i);
            cmul(&l, &l, &z); mpf_mul_2exp(l.r, l.r, 1); mpf_mul_2exp(l.i, l.i, 1);
            cdiv(&w, &one, &l); mpf_add(b.r, b.r, w.r); mpf_add(b.i, b.i, w.i);
        }
        cmul(&w, &l, &l); cmul(&w, &w, &b); cdiv(&k, &one, &w);
        fprintf(stderr, "level %d: period %ld  |size| 1e%.2f\n", lev + 1, period, clog10(&k));
    }
    int digs = (int)(bits * 0.30103) - 5;
    printf("%ld\n", period);
    gmp_printf("%.*Fe\n%.*Fe\n%.*Fe\n%.*Fe\n", digs, c.r, digs, c.i, 20, k.r, 20, k.i);
    return 0;
}
