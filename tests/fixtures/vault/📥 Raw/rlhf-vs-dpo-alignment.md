---
source: https://magazine.sebastianrisi.com/rlhf-vs-dpo
canonical_url: https://magazine.sebastianrisi.com/rlhf-vs-dpo
title: "RLHF vs DPO: A Comparison of Alignment Methods"
tags: [rlhf, dpo, alignment, llm-training, reinforcement-learning]
author: Sebastian Risi
saved: 2026-05-12T09:15:00+00:00
type: article
rating: 8
vaultmind: false
---

# RLHF vs DPO: A Comparison of Alignment Methods

## The Alignment Problem

Large language models are trained to predict the next token on vast text corpora. This pre-training objective doesn't inherently align the model with human preferences. **Reinforcement Learning from Human Feedback (RLHF)** was introduced to bridge this gap.

## How RLHF Works

RLHF involves three stages:

1. **Supervised Fine-Tuning (SFT)**: Fine-tune the pre-trained model on high-quality demonstration data
2. **Reward Model Training**: Train a reward model on human preference comparisons
3. **RL Optimization**: Use PPO (Proximal Policy Optimization) to maximize the reward signal

The final stage uses the reward model to guide policy updates, but this is notoriously unstable and sensitive to hyperparameters.

## Direct Preference Optimization (DPO)

DPO reframes alignment as a classification problem rather than a reinforcement learning problem. Instead of training a separate reward model, DPO directly optimizes the policy using preference pairs.

The key insight: the implicit reward from DPO can be computed directly from the policy and reference distributions:

```
r(x, y) = β * log(π(y|x) / π_ref(y|x))
```

## Comparison

| Aspect | RLHF | DPO |
|--------|------|-----|
| Training stability | Requires PPO tuning | Stable, no RL |
| Sample efficiency | Lower | Higher |
| Computational cost | High (needs reward model) | Lower |
| Memory usage | High (requires PPO buffer) | Lower |

## When to Use Which

- **RLHF**: When you have a well-calibrated reward model and need fine-grained control
- **DPO**: When alignment data is limited and simplicity is preferred

## Limitations of Both

Neither method solves fundamental issues:
- Reward hacking remains possible
- Human preferences are inconsistent and context-dependent
- Distribution shift between training and deployment

## Open Questions

- Can we combine RLHF and DPO for best of both worlds?
- How do these methods scale with model size?
- What are the theoretical guarantees on out-of-distribution inputs?

![alignment diagram](https://magazine.sebastianrisi.com/assets/rlhf_diagram.png)

## Sources

- [DeepMind's DPO Paper](https://arxiv.org/abs/2305.18290)
- [Anthropic's RLHF Tutorial](https://www.anthropic.com/research/constitutional-ai)
