import numpy as np
import matplotlib.pyplot as plt

d = np.load("logs/evaluations.npz")
steps = d["timesteps"]
res = d["results"]                     # alakja: (kiértékelések száma, epizódok száma)
mean, std = res.mean(axis=1), res.std(axis=1)

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(steps / 1e6, mean, color="tab:blue", label="Átlagos jutalom (10 epizód)")
ax.fill_between(steps / 1e6, mean - std, mean + std, color="tab:blue", alpha=0.2, label="± szórás")
ax.set_xlabel("Tanítási lépések (millió)")
ax.set_ylabel("Átlagos epizódjutalom")
ax.grid(alpha=0.3)
ax.legend(loc="lower right")
fig.tight_layout()
fig.savefig("tanitasi_gorbe.png", dpi=200)
print("kész: tanitasi_gorbe.png")