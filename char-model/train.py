"""Train a tiny character-level language model on corpus.txt and record samples per epoch.

    uv run --no-project --with torch --index https://download.pytorch.org/whl/cpu \
        python char-model/train.py
"""

import json
import math
import time
from pathlib import Path

import torch
from torch import nn

HERE = Path(__file__).parent
SEQ, BATCH, HIDDEN, LAYERS, EMBED = 128, 256, 256, 2, 32
EPOCHS, LR = 100, 5e-3
SAMPLE_AT = [0, 1, 5, 10, 100]
SEED_TEXT, SAMPLE_LEN, TEMPERATURE, N_SAMPLES = "c", 240, 0.8, 3

torch.manual_seed(0)
torch.set_num_threads(8)  # more threads is slower for a model this small
text = (HERE / "corpus.txt").read_text()
vocab = sorted(set(text))
stoi = {c: i for i, c in enumerate(vocab)}
data = torch.tensor([stoi[c] for c in text])
split = int(len(data) * 0.95)
train, val = data[:split], data[split:]


class CharModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.embed = nn.Embedding(len(vocab), EMBED)
        self.rnn = nn.GRU(EMBED, HIDDEN, LAYERS, batch_first=True)
        self.head = nn.Linear(HIDDEN, len(vocab))

    def forward(self, x, h=None):
        out, h = self.rnn(self.embed(x), h)
        return self.head(out), h


def batches(d: torch.Tensor, shuffle: bool):
    """One epoch = every character seen once, in SEQ-long windows."""
    offset = int(torch.randint(SEQ, (1,))) if shuffle else 0
    n = (len(d) - offset - 1) // SEQ
    x = d[offset : offset + n * SEQ].view(n, SEQ)
    y = d[offset + 1 : offset + 1 + n * SEQ].view(n, SEQ)
    order = torch.randperm(n) if shuffle else torch.arange(n)
    for i in range(0, n, BATCH):
        idx = order[i : i + BATCH]
        yield x[idx], y[idx]


@torch.no_grad()
def evaluate(model) -> float:
    model.eval()
    losses = [loss_fn(model(x)[0].transpose(1, 2), y).item() for x, y in batches(val, False)]
    model.train()
    return sum(losses) / len(losses)


@torch.no_grad()
def sample(model, seed: int) -> str:
    """Generate one character at a time, feeding each prediction back in."""
    model.eval()
    g = torch.Generator().manual_seed(seed)
    out, h = SEED_TEXT, None
    x = torch.tensor([[stoi[c] for c in SEED_TEXT]])
    for _ in range(SAMPLE_LEN):
        logits, h = model(x, h)
        probs = torch.softmax(logits[0, -1] / TEMPERATURE, dim=-1)
        c = vocab[int(torch.multinomial(probs, 1, generator=g))]
        if c == "\n":
            break
        out += c
        x = torch.tensor([[stoi[c]]])
    model.train()
    return out


model = CharModel()
loss_fn = nn.CrossEntropyLoss()
opt = torch.optim.Adam(model.parameters(), lr=LR)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, EPOCHS)
results = {
    "params": sum(p.numel() for p in model.parameters()),
    "chars": len(text),
    "listings": text.count("\n"),
    "vocab": len(vocab),
    "config": {"seq": SEQ, "batch": BATCH, "hidden": HIDDEN, "layers": LAYERS, "epochs": EPOCHS},
    "losses": [],
    "samples": {},
}
print(f"{results['params']:,} params · {len(text):,} chars · vocab {len(vocab)}")
results["samples"]["0"] = [sample(model, s) for s in range(N_SAMPLES)]

start = time.time()
for epoch in range(1, EPOCHS + 1):
    total, steps = 0.0, 0
    for x, y in batches(train, True):
        logits, _ = model(x)
        loss = loss_fn(logits.transpose(1, 2), y)
        opt.zero_grad()
        loss.backward()  # backpropagation
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        total, steps = total + loss.item(), steps + 1
    sched.step()
    val_loss = evaluate(model)
    results["losses"].append({"epoch": epoch, "train": total / steps, "val": val_loss})
    print(f"epoch {epoch:3d}  train {total / steps:.3f}  val {val_loss:.3f}  ppl {math.exp(val_loss):.1f}  {time.time() - start:.0f}s")
    if epoch in SAMPLE_AT:
        results["samples"][str(epoch)] = [sample(model, s) for s in range(N_SAMPLES)]
        for s in results["samples"][str(epoch)]:
            print("   ", s)

results["seconds"] = round(time.time() - start)
(HERE / "results.json").write_text(json.dumps(results, indent=2))
