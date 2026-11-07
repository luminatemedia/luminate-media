#!/usr/bin/env python3
"""Syntetiserar ljudet till Luminate-logo-revealen (brand/logo-reveal/).

Inga samplingar eller licenser: allt genereras med numpy.
Tidpunkterna nedan matchar tidslinjen `T` i brand/logo-reveal/index.html.

    python3 scripts/logo_reveal_audio.py brand/logo-reveal/luminate-logo-reveal.wav
"""
import sys
import wave

import numpy as np

SR = 48000
DUR = 6.5
T_STREAK = 0.05
T_SLAM = (1.42, 1.90)
T_IMPACT = 1.90
T_GLINTS = (2.20, 5.05)
T_LIFT = (2.55, 3.35)
T_LETTERS = 2.78
T_MEDIA = 3.45

n = int(SR * DUR)
t = np.arange(n) / SR
rng = np.random.default_rng(7)
dry = np.zeros((n, 2))
wet = np.zeros((n, 2))  # skickas till reverb


def seg(t0, t1):
    a, b = int(t0 * SR), min(n, int(t1 * SR))
    return slice(a, b), (np.arange(b - a) / SR)


def fft_filter(x, lo=None, hi=None):
    """Mjukt band-/hög-/lågpass i frekvensdomänen."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if lo:
        g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** 4)
    if hi:
        g *= 1 / np.sqrt(1 + (f / hi) ** 4)
    return np.fft.irfft(X * g, len(x))


def svf_bandpass(x, fc, q=2.0):
    """Tidsvarierande state-variable bandpass (fc = array i Hz)."""
    y = np.zeros_like(x)
    lp = bp = 0.0
    damp = 1 / q
    for i in range(len(x)):
        f = 2 * np.sin(np.pi * min(fc[i], SR / 6) / SR)
        hp = x[i] - lp - damp * bp
        bp += f * hp
        lp += f * bp
        y[i] = bp
    return y


def pan(sig, p):
    """p: -1 (vänster) .. 1 (höger), skalär eller array."""
    p = np.asarray(p)
    a = (p + 1) * np.pi / 4
    return np.stack([sig * np.cos(a), sig * np.sin(a)], axis=1)


def add(buf, s, stereo):
    buf[s.start:s.start + len(stereo)] += stereo


# 1) ljusstreck: luftig shimmer
s, tt = seg(T_STREAK, 1.3)
env = np.minimum(tt / 0.35, 1) * np.exp(-np.maximum(tt - 0.35, 0) / 0.3)
sh = sum(np.sin(2 * np.pi * f * tt + ph) for f, ph in ((2637, 0), (3524, 1.3), (4186, 2.1), (5274, .4)))
sh *= 0.5 + 0.5 * np.sin(2 * np.pi * 9 * tt)
air = fft_filter(rng.standard_normal(len(tt)), lo=5000)
add(wet, s, pan(0.012 * sh * env + 0.03 * air * env, np.sin(tt * 3) * 0.6))

# 2) riser in mot smällen (brus med stigande bandpass + svepande ton)
s, tt = seg(0.45, T_IMPACT)
L = tt[-1]
x = tt / L
fc = 180 * (5200 / 180) ** (x ** 1.6)
noise = svf_bandpass(rng.standard_normal(len(tt)), fc, q=3.0)
tone = np.sin(2 * np.pi * np.cumsum(140 * (950 / 140) ** (x ** 2)) / SR)
amp = x ** 3.2
cut = np.minimum((L - tt) / 0.004, 1)  # hårt stopp precis vid nedslaget
riser = (0.22 * noise + 0.08 * tone) * amp * cut
add(dry, s, pan(riser, 0))
add(wet, s, pan(0.5 * riser, 0))

# 3) whoosh när bitarna flyger in (L från vänster, M från höger)
s, tt = seg(*T_SLAM)
x = tt / tt[-1]
for side in (-1, 1):
    w = svf_bandpass(rng.standard_normal(len(tt)), 500 * (3500 / 500) ** x, q=1.4)
    add(dry, s, pan(0.32 * w * x ** 2.5 * np.minimum((tt[-1] - tt) / 0.003, 1), side * (1 - x) * 0.9))

# 4) nedslaget
s, tt = seg(T_IMPACT, DUR)
freq = 38 + 72 * np.exp(-tt * 5)
sub = np.tanh(1.6 * np.sin(2 * np.pi * np.cumsum(freq) / SR)) * np.exp(-tt / 0.85)
click = fft_filter(rng.standard_normal(len(tt)), lo=2500) * np.exp(-tt / 0.006)
body = fft_filter(rng.standard_normal(len(tt)), hi=900) * np.exp(-tt / 0.22)
crack = fft_filter(rng.standard_normal(len(tt)), lo=1500, hi=9000) * np.exp(-tt / 0.07)
add(dry, s, pan(0.95 * sub + 0.45 * click + 0.5 * body, 0))
add(dry, s, np.stack([0.35 * crack, 0.35 * np.roll(crack, 37)], axis=1))
add(wet, s, pan(0.5 * body + 0.4 * crack + 0.25 * click, 0))
# metallisk efterklang
bell = np.zeros((len(tt), 2))
for f, a, p in ((523.3, .5, -.5), (784.0, .4, .5), (1046.5, .3, -.2), (1568.0, .2, .3), (2093, .12, 0)):
    bell += pan(a * np.sin(2 * np.pi * f * 1.0007 * tt) * np.exp(-tt / (2.2 - f / 2000)), p)
add(wet, s, 0.05 * bell)

# 5) varm pad efter smällen (E-dur, mjukt lågpassad)
s, tt = seg(T_IMPACT, DUR)
pad = np.zeros(len(tt))
for f in (82.41, 123.47, 164.81, 207.65, 246.94, 329.63):
    for det in (-0.12, 0.12):
        ff = f * 2 ** (det / 12)
        pad += sum(np.sin(2 * np.pi * ff * h * tt) / h ** 1.6 for h in (1, 2, 3))
pad = fft_filter(pad, hi=1400)
penv = np.minimum(tt / 0.9, 1) * np.minimum((DUR - T_IMPACT - tt) / 0.9, 1)
pad *= penv * (0.85 + 0.15 * np.sin(2 * np.pi * 0.3 * tt))
pad /= np.abs(pad).max() + 1e-9
add(dry, s, pan(0.11 * pad, 0))
add(wet, s, np.stack([0.06 * pad, 0.06 * np.roll(pad, 600)], axis=1))

# 6) glint-shimmer
for g0 in T_GLINTS:
    s, tt = seg(g0, g0 + 1.2)
    x = np.minimum(tt / 0.75, 1)
    f = 2600 * (6200 / 2600) ** x
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 14 * tt))
    env = np.sin(np.pi * x) ** 2 * (tt < 0.75)
    add(wet, s, pan(0.035 * sig * env, (x - 0.5) * 1.4))
    # liten "ping" när stjärnan blinkar
    s2, t2 = seg(g0 + 0.55, g0 + 2.5)
    add(wet, s2, pan(0.05 * np.sin(2 * np.pi * 3951 * t2) * np.exp(-t2 / 0.5), 0.5))

# 7) lyft-whoosh
s, tt = seg(*T_LIFT)
x = tt / tt[-1]
w = svf_bandpass(rng.standard_normal(len(tt)), 2400 * (400 / 2400) ** x, q=1.2)
add(dry, s, pan(0.12 * w * np.sin(np.pi * x) ** 2, 0))

# 8) bokstavs-tick (LUMINATE), panorerade vänster -> höger
for i in range(8):
    t0 = T_LETTERS + i * 0.055
    s, tt = seg(t0, t0 + 0.12)
    tick = np.sin(2 * np.pi * (2200 + 90 * i) * tt) * np.exp(-tt / 0.018)
    tick += 0.6 * fft_filter(rng.standard_normal(len(tt)), lo=4000) * np.exp(-tt / 0.004)
    st = pan(0.11 * tick, -0.7 + i * 0.2)
    add(dry, s, st)
    add(wet, s, 0.6 * st)

# 9) "Media"-klocka
s, tt = seg(T_MEDIA, DUR)
chime = sum(a * np.sin(2 * np.pi * f * tt) for f, a in ((659.25, 1), (987.77, .6), (1318.5, .35)))
chime *= np.exp(-tt / 1.1) * np.minimum(tt / 0.01, 1)
add(dry, s, pan(0.05 * chime, 0))
add(wet, s, pan(0.08 * chime, 0))

# reverb: faltning med avklingande stereobrus (FFT)
ir_len = int(2.6 * SR)
ti = np.arange(ir_len) / SR
mix = dry.copy()
for ch in range(2):
    ir = fft_filter(rng.standard_normal(ir_len), lo=200, hi=7000) * np.exp(-ti / 0.7)
    ir[: int(0.012 * SR)] = 0  # predelay
    ir /= np.sqrt((ir ** 2).sum())
    m = n + ir_len
    rev = np.fft.irfft(np.fft.rfft(wet[:, ch], m) * np.fft.rfft(ir, m), m)[:n]
    mix[:, ch] += wet[:, ch] * 0.6 + rev * 0.9

# master: mjuk limiter + normalisering + fade ut
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix *= np.minimum((DUR - t) / 0.35, 1)[:, None]
mix /= np.abs(mix).max() / 0.89

out = sys.argv[1] if len(sys.argv) > 1 else 'luminate-logo-reveal.wav'
with wave.open(out, 'wb') as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
print('wrote', out)
