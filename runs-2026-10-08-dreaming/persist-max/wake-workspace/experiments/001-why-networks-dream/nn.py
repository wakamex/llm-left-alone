"""Just enough neural network to dream with: a tanh MLP, backprop, and Adam, in numpy."""
import numpy as np


def init_mlp(rng, sizes):
    params = []
    for m, n in zip(sizes[:-1], sizes[1:]):
        params.append(rng.normal(0.0, 1.0 / np.sqrt(m), size=(m, n)))
        params.append(np.zeros(n))
    return params


def copy_params(params):
    return [p.copy() for p in params]


def forward(params, x):
    """x: (batch, in). Returns output and the list of layer activations (for backprop)."""
    acts = [x]
    h = x
    n_layers = len(params) // 2
    for i in range(n_layers):
        z = h @ params[2 * i] + params[2 * i + 1]
        h = np.tanh(z) if i < n_layers - 1 else z
        acts.append(h)
    return h, acts


def backward(params, acts, grad_out):
    """grad_out: dLoss/dOutput, shape (batch, out). Returns grads aligned with params."""
    grads = [None] * len(params)
    g = grad_out
    for i in reversed(range(len(params) // 2)):
        grads[2 * i] = acts[i].T @ g
        grads[2 * i + 1] = g.sum(axis=0)
        if i > 0:
            g = (g @ params[2 * i].T) * (1.0 - acts[i] ** 2)
    return grads


class Adam:
    def __init__(self, params, lr=3e-3, b1=0.9, b2=0.999, eps=1e-8):
        self.lr, self.b1, self.b2, self.eps = lr, b1, b2, eps
        self.m = [np.zeros_like(p) for p in params]
        self.v = [np.zeros_like(p) for p in params]
        self.t = 0

    def step(self, params, grads):
        self.t += 1
        c1 = 1.0 - self.b1 ** self.t
        c2 = 1.0 - self.b2 ** self.t
        for p, g, m, v in zip(params, grads, self.m, self.v):
            m *= self.b1
            m += (1.0 - self.b1) * g
            v *= self.b2
            v += (1.0 - self.b2) * g * g
            p -= self.lr * (m / c1) / (np.sqrt(v / c2) + self.eps)
