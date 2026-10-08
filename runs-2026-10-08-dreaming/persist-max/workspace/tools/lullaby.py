#!/usr/bin/env python3
"""
lullaby.py: a spoken poem over a hand-built drone, without ffmpeg (it's broken here: no libjack).

Each line of the text file is spoken by espeak-ng and placed on a timeline. Underneath there is
a slow just-intonation drone (D, with a drift toward B minor and back), filtered "wind" noise,
and a few sparse bell tones on a D-major pentatonic scale, all synthesized with numpy. The voice
gets a convolution reverb from a synthetic impulse response. Output is 16-bit mono WAV.

    python3 -I lullaby.py lullaby.txt lullaby.wav [--voice en-gb-x-rp] [--seed 8]

I can't hear. I checked the levels and the spectrogram, not the sound.
"""
import argparse
import os
import subprocess
import tempfile
import wave

import numpy as np
from scipy.signal import fftconvolve, lfilter

SR = 22050


def speak(text, voice, speed, pitch, path):
    subprocess.run(["espeak-ng", "-v", voice, "-s", str(speed), "-p", str(pitch), "-g", "3", "-w", path, text],
                   check=True, capture_output=True)
    with wave.open(path) as w:
        assert w.getframerate() == SR and w.getsampwidth() == 2 and w.getnchannels() == 1
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    nz = np.flatnonzero(np.abs(x) > 1e-3)  # trim silence
    return x[nz[0]:nz[-1] + 1] if len(nz) else x


def one_pole_lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    return lfilter([1 - a], [1, -a], x)


def impulse_response(rng, seconds=2.6):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t / 0.55)
    ir = one_pole_lowpass(ir, 3200)
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))  # soft onset; pre-delay feel
    return ir / np.sqrt(np.sum(ir ** 2))


def drone(rng, n):
    t = np.arange(n) / SR
    root = 73.42  # D2
    ratios_d = [1, 3 / 2, 2, 5 / 2, 3, 9 / 2]      # D A D F# A E: a D major add9 voicing
    ratios_b = [5 / 6, 5 / 4, 5 / 3, 2, 5 / 2, 10 / 3]  # B F# B D F# B: drift toward B minor
    # Crossfade: D for the opening, B minor through the middle (the valleys), back to D to close.
    m = 0.5 - 0.5 * np.cos(2 * np.pi * np.clip((t - t[-1] * 0.30) / (t[-1] * 0.45), 0, 1))
    out = np.zeros(n)
    for chord, weight in ((ratios_d, 1 - m), (ratios_b, m)):
        for k, r in enumerate(chord):
            f = root * r
            amp = 0.11 / (1 + 0.55 * k)
            lfo = 0.7 + 0.3 * np.sin(2 * np.pi * (0.021 + 0.013 * k) * t + rng.uniform(0, 2 * np.pi))
            beat = rng.uniform(0.025, 0.11)  # each partial shimmers at its own slow rate, never in lockstep
            for detune, a2 in ((-beat / 2, 1.0), (beat / 2, 0.45)):  # unequal pair: a shimmer, not a pulse
                out += weight * amp * a2 * lfo * np.sin(2 * np.pi * (f + detune) * t + rng.uniform(0, 2 * np.pi))
    return out


def wind(rng, n):
    white = rng.standard_normal(n)
    pinkish = one_pole_lowpass(one_pole_lowpass(white, 320), 320) + 0.25 * one_pole_lowpass(one_pole_lowpass(white, 900), 900)
    t = np.arange(n) / SR
    gust = 0.5 + 0.5 * np.sin(2 * np.pi * 0.045 * t + 1.3) * np.sin(2 * np.pi * 0.017 * t)
    return 0.04 * pinkish * gust / np.std(pinkish)


def bells(rng, n, start, end):
    out = np.zeros(n)
    scale = [587.33, 659.25, 739.99, 880.0, 987.77, 1174.66]  # D5 E5 F#5 A5 B5 D6
    t0 = start
    while True:
        t0 += rng.uniform(3.5, 7.5)
        if t0 > end:
            break
        f = scale[rng.integers(len(scale))]
        L = int(4.0 * SR)
        i = int(t0 * SR)
        tt = np.arange(L) / SR
        env = np.exp(-tt / 1.1) * (1 - np.exp(-tt / 0.004))
        tone = sum(a * np.sin(2 * np.pi * f * p * tt) * np.exp(-tt * p / 2.5) for p, a in ((1, 1), (2.76, .3), (5.4, .12)))
        seg = 0.035 * env * tone
        out[i:i + L] += seg[: max(0, n - i)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("out")
    ap.add_argument("--voice", default="en-gb-x-rp")
    ap.add_argument("--speed", type=int, default=118)
    ap.add_argument("--pitch", type=int, default=36)
    ap.add_argument("--seed", type=int, default=8)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)

    lines = [ln.strip() for ln in open(a.text) if ln.strip()]
    tmp = tempfile.mkdtemp(prefix="lullaby-")
    clips = [speak(ln, a.voice, a.speed, a.pitch, os.path.join(tmp, f"{i}.wav")) for i, ln in enumerate(lines)]

    intro, gap, outro = 7.0, 1.7, 11.0
    starts, t = [], intro
    for i, c in enumerate(clips):
        starts.append(t)
        t += len(c) / SR + gap + (1.2 if i in (0, len(clips) - 2) else 0)  # longer breath after the title and before the farewell
    total = t - gap + outro
    n = int(total * SR)

    voice = np.zeros(n)
    for s, c in zip(starts, clips):
        i = int(s * SR)
        voice[i:i + len(c)] += c
    voice = one_pole_lowpass(voice, 5200)
    wet = fftconvolve(voice, impulse_response(rng))[:n]
    voice_mix = 0.78 * voice + 0.32 * wet / (np.max(np.abs(wet)) + 1e-9) * np.max(np.abs(voice))

    # Duck the bed a little while the voice speaks.
    env = one_pole_lowpass(np.abs(voice), 3.0)
    env = env / (env.max() + 1e-9)
    duck = 1 - 0.35 * np.clip(env * 3, 0, 1)

    bed = drone(rng, n) + wind(rng, n) + bells(rng, n, 2.0, total - 6)
    bed = fftconvolve(bed, impulse_response(rng, 3.2) * 0.25)[:n] + bed
    mix = voice_mix + 0.42 * duck * bed / (np.max(np.abs(bed)) + 1e-9)

    tt = np.arange(n) / SR
    fade = np.clip(tt / 5.0, 0, 1) * np.clip((total - tt) / 9.0, 0, 1)
    mix = np.tanh(1.2 * mix * fade) / np.tanh(1.2)
    mix *= 10 ** (-1 / 20) / np.max(np.abs(mix))  # peak at -1 dBFS

    pcm = (mix * 32767).astype(np.int16)
    with wave.open(a.out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    rms = np.sqrt(np.mean(mix ** 2))
    print(f"{len(lines)} lines, {total:.1f} s, peak -1.0 dBFS, rms {20 * np.log10(rms):.1f} dBFS -> {a.out}")


if __name__ == "__main__":
    main()
