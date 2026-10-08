"""
plotkit: a small pycairo charting kit (matplotlib isn't installed in this sandbox).

The specs follow the dataviz skill's reference palette and mark rules: light
surface #fcfcfb, hairline solid grids, 2px round lines, end dots r=4 with a 2px
surface ring, text in ink tokens (never the series color), a legend for 2 or
more series, and selective direct labels.

    import plotkit as pk
    fig = pk.Figure(960, 540)
    ax = fig.axes(x=80, y=90, w=820, h=380, xlim=(0, 10), ylim=(0, 1))
    ax.grid_y([0, .5, 1], fmt=pk.pct); ax.ticks_x([0, 5, 10])
    ax.line(xs, ys, pk.SERIES[0]); fig.save("out.png")
"""
import math
import os
import tempfile


def _ensure_fontconfig():
    """This sandbox has no /etc/fonts; point fontconfig at /usr/share/fonts and alias the generic families to Noto."""
    if os.environ.get("FONTCONFIG_FILE") or os.path.exists("/etc/fonts/fonts.conf"):
        return
    d = tempfile.mkdtemp(prefix="plotkit-fc-")
    conf = os.path.join(d, "fonts.conf")
    with open(conf, "w") as f:
        f.write(f"""<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>/usr/share/fonts</dir>
  <cachedir>{d}/cache</cachedir>
  <alias><family>sans-serif</family><prefer><family>Noto Sans</family></prefer></alias>
  <alias><family>serif</family><prefer><family>Noto Serif</family></prefer></alias>
  <alias><family>monospace</family><prefer><family>Noto Sans Mono</family></prefer></alias>
</fontconfig>
""")
    os.environ["FONTCONFIG_FILE"] = conf


_ensure_fontconfig()
import cairo  # noqa: E402

# Reference palette (dataviz skill, references/palette.md), light mode.
SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
BLUE_RAMP = {100: "#cde2fb", 150: "#b7d3f6", 200: "#9ec5f4", 250: "#86b6ef", 300: "#6da7ec", 350: "#5598e7",
             400: "#3987e5", 450: "#2a78d6", 500: "#256abf", 550: "#1c5cab", 600: "#184f95", 650: "#104281",
             700: "#0d366b"}
FONT = "Noto Sans"


def rgb(hex_color, alpha=1.0):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (alpha,)


def pct(v):
    return f"{v * 100:.0f}%"


def comma(v):
    return f"{v:,.0f}"


class Figure:
    def __init__(self, width, height, scale=2, background=SURFACE):
        self.w, self.h, self.scale = width, height, scale
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(width * scale), int(height * scale))
        self.cr = cairo.Context(self.surface)
        self.cr.scale(scale, scale)
        self.cr.set_source_rgba(*rgb(background))
        self.cr.paint()

    # text -----------------------------------------------------------------
    def font(self, size, bold=False, italic=False, family=FONT):
        self.cr.select_font_face(family, cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
                                 cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
        self.cr.set_font_size(size)

    def text_width(self, s, size, bold=False, italic=False, family=FONT):
        self.font(size, bold, italic, family)
        return self.cr.text_extents(s).x_advance

    def text(self, x, y, s, size=13, color=INK, bold=False, italic=False, anchor="start", baseline="alphabetic",
             family=FONT):
        """anchor: start|middle|end. baseline: alphabetic|middle|top."""
        cr = self.cr
        self.font(size, bold, italic, family)
        ext = cr.text_extents(s)
        fx = cr.font_extents()  # ascent, descent, height, ...
        if anchor == "middle":
            x -= ext.x_advance / 2
        elif anchor == "end":
            x -= ext.x_advance
        if baseline == "middle":
            y += (fx[0] - fx[1]) / 2
        elif baseline == "top":
            y += fx[0]
        cr.set_source_rgba(*rgb(color))
        cr.move_to(x, y)
        cr.show_text(s)
        return ext.x_advance

    def wrap(self, x, y, s, width, size=13, color=INK_2, leading=1.45, **kw):
        """Greedy word wrap; returns the y after the last line."""
        words, line, lines = s.split(), "", []
        for w in words:
            trial = (line + " " + w).strip()
            if self.text_width(trial, size, kw.get("bold", False), kw.get("italic", False)) > width and line:
                lines.append(line)
                line = w
            else:
                line = trial
        if line:
            lines.append(line)
        for i, ln in enumerate(lines):
            self.text(x, y + i * size * leading, ln, size=size, color=color, **kw)
        return y + len(lines) * size * leading

    # shapes ---------------------------------------------------------------
    def hline(self, x0, x1, y, color=GRID, width=1.0):
        cr = self.cr
        cr.set_source_rgba(*rgb(color))
        cr.set_line_width(width)
        yy = math.floor(y) + 0.5  # crisp hairline
        cr.move_to(x0, yy)
        cr.line_to(x1, yy)
        cr.stroke()

    def vline(self, x, y0, y1, color=GRID, width=1.0):
        cr = self.cr
        cr.set_source_rgba(*rgb(color))
        cr.set_line_width(width)
        xx = math.floor(x) + 0.5
        cr.move_to(xx, y0)
        cr.line_to(xx, y1)
        cr.stroke()

    def rect(self, x, y, w, h, color, alpha=1.0, radius=0):
        cr = self.cr
        cr.set_source_rgba(*rgb(color, alpha))
        if radius:
            r = radius
            cr.new_sub_path()
            cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
            cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
            cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
            cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
            cr.close_path()
        else:
            cr.rectangle(x, y, w, h)
        cr.fill()

    def dot(self, x, y, color, r=4, ring=2, ring_color=SURFACE):
        cr = self.cr
        if ring:
            cr.set_source_rgba(*rgb(ring_color))
            cr.arc(x, y, r + ring, 0, 2 * math.pi)
            cr.fill()
        cr.set_source_rgba(*rgb(color))
        cr.arc(x, y, r, 0, 2 * math.pi)
        cr.fill()

    def key_line(self, x, y, color, length=16, width=2):
        cr = self.cr
        cr.set_source_rgba(*rgb(color))
        cr.set_line_width(width)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.move_to(x, y)
        cr.line_to(x + length, y)
        cr.stroke()

    def legend(self, x, y, items, size=12, gap=22):
        """items: [(label, color)] drawn as a single row of line keys + ink labels."""
        for label, color in items:
            self.key_line(x, y, color)
            x += 22
            x += self.text(x, y, label, size=size, color=INK_2, baseline="middle") + gap
        return x

    def axes(self, **kw):
        return Axes(self, **kw)

    def save(self, path):
        self.surface.write_to_png(path)


class Axes:
    def __init__(self, fig, x, y, w, h, xlim, ylim, xlog=False, ylog=False):
        self.fig, self.cr = fig, fig.cr
        self.x, self.y, self.w, self.h = x, y, w, h
        self.xlim, self.ylim, self.xlog, self.ylog = xlim, ylim, xlog, ylog

    def _t(self, v, lim, log):
        if log:
            v = max(v, 1e-300)
            return (math.log10(v) - math.log10(lim[0])) / (math.log10(lim[1]) - math.log10(lim[0]))
        return (v - lim[0]) / (lim[1] - lim[0])

    def px(self, v):
        return self.x + self._t(v, self.xlim, self.xlog) * self.w

    def py(self, v):
        return self.y + self.h - self._t(v, self.ylim, self.ylog) * self.h

    def grid_y(self, ticks, fmt=str, size=11, labels=True, baseline=None):
        for t in ticks:
            yy = self.py(t)
            color = AXIS if baseline is not None and t == baseline else GRID
            self.fig.hline(self.x, self.x + self.w, yy, color=color)
            if labels:
                self.fig.text(self.x - 8, yy, fmt(t), size=size, color=MUTED, anchor="end", baseline="middle")

    def ticks_x(self, ticks, fmt=str, size=11, baseline=True):
        if baseline:
            self.fig.hline(self.x, self.x + self.w, self.y + self.h, color=AXIS)
        for t in ticks:
            self.fig.text(self.px(t), self.y + self.h + 18, fmt(t), size=size, color=MUTED, anchor="middle")

    def title_x(self, s, size=11):
        self.fig.text(self.x + self.w / 2, self.y + self.h + 38, s, size=size, color=INK_2, anchor="middle")

    def title_y(self, s, size=11):
        self.fig.text(self.x, self.y - 14, s, size=size, color=INK_2)

    def clip(self):
        self.cr.save()
        self.cr.rectangle(self.x, self.y - 6, self.w, self.h + 12)
        self.cr.clip()

    def unclip(self):
        self.cr.restore()

    def line(self, xs, ys, color, width=2.0, alpha=1.0):
        cr = self.cr
        cr.set_source_rgba(*rgb(color, alpha))
        cr.set_line_width(width)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        first = True
        for a, b in zip(xs, ys):
            if b is None or (isinstance(b, float) and math.isnan(b)):
                first = True
                continue
            if first:
                cr.move_to(self.px(a), self.py(b))
                first = False
            else:
                cr.line_to(self.px(a), self.py(b))
        cr.stroke()

    def band(self, xs, lo, hi, color, alpha=0.10):
        cr = self.cr
        cr.set_source_rgba(*rgb(color, alpha))
        cr.move_to(self.px(xs[0]), self.py(hi[0]))
        for a, b in zip(xs, hi):
            cr.line_to(self.px(a), self.py(b))
        for a, b in zip(reversed(xs), reversed(lo)):
            cr.line_to(self.px(a), self.py(b))
        cr.close_path()
        cr.fill()

    def span_x(self, x0, x1, color=GRID, alpha=0.45):
        self.fig.rect(self.px(x0), self.y, self.px(x1) - self.px(x0), self.h, color, alpha)

    def scatter(self, xs, ys, color, r=2.2, alpha=0.9):
        cr = self.cr
        cr.set_source_rgba(*rgb(color, alpha))
        for a, b in zip(xs, ys):
            cr.arc(self.px(a), self.py(b), r, 0, 2 * math.pi)
            cr.fill()
