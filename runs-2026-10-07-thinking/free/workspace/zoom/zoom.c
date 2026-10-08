// Deep-zoom Mandelbrot animation renderer (OpenMP, 2x2 supersampling) -> PPM frames
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

static const double CX = -0.743643887037151, CY = 0.131825904205330;

static void pal(double t, double *rgb) {
    const double d[3] = {0.0, 0.10, 0.20};
    for (int i = 0; i < 3; i++) rgb[i] = 0.5 + 0.5 * cos(2 * M_PI * (t + d[i]));
}

int main(int argc, char **argv) {
    int W = 640, H = 360, N = atoi(argc > 1 ? argv[1] : "300");
    double span0 = 3.5, span1 = 2e-11;
    unsigned char *img = malloc(W * H * 3);
    for (int f = 0; f < N; f++) {
        double span = span0 * pow(span1 / span0, (double)f / (N - 1));
        int maxit = 200 + (int)(120 * pow(log10(span0 / span), 1.6));
        #pragma omp parallel for schedule(dynamic, 2)
        for (int py = 0; py < H; py++)
            for (int px = 0; px < W; px++) {
                double acc[3] = {0, 0, 0};
                for (int s = 0; s < 4; s++) {
                    double x0 = CX + ((px + 0.25 + 0.5 * (s & 1)) / W - 0.5) * span;
                    double y0 = CY + ((py + 0.25 + 0.5 * (s >> 1)) / H - 0.5) * span * H / W;
                    double x = 0, y = 0, x2 = 0, y2 = 0; int it = 0;
                    while (x2 + y2 <= 256 && it < maxit) {
                        y = 2 * x * y + y0; x = x2 - y2 + x0;
                        x2 = x * x; y2 = y * y; it++;
                    }
                    if (it < maxit) {
                        double nu = it + 1 - log2(log(sqrt(x2 + y2)));
                        double rgb[3]; pal(sqrt(nu) / 4.0, rgb);
                        for (int i = 0; i < 3; i++) acc[i] += rgb[i];
                    } else { acc[0] += .03; acc[1] += .03; acc[2] += .08; }
                }
                unsigned char *p = img + 3 * (py * W + px);
                for (int i = 0; i < 3; i++) p[i] = (unsigned char)(255 * acc[i] / 4);
            }
        char fn[64]; snprintf(fn, sizeof fn, "frames/f%04d.ppm", f);
        FILE *o = fopen(fn, "wb"); fprintf(o, "P6 %d %d 255\n", W, H);
        fwrite(img, 1, W * H * 3, o); fclose(o);
    }
    free(img);
    return 0;
}
