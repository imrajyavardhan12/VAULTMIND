---
source: https://blog.research.google/2023/03/encouraging-sparse-attention-in.html
canonical_url: https://blog.research.google/2023/03/encouraging-sparse-attention-in.html
title: "Sparse Attention Trade-offs in Transformer Models"
tags: [transformers, sparse-attention, efficiency, google-research]
author: Google Research
saved: 2026-05-14T11:00:00+00:00
type: article
rating: 7
vaultmind: false
---

# Sparse Attention Trade-offs in Transformer Models

## Motivation

Standard self-attention has O(n²) complexity in sequence length. For tasks requiring long contexts (document-level NLP, genomics, code comprehension), this becomes a bottleneck. **Sparse attention** methods aim to reduce this to O(n · k) where k is a small constant number of non-zero entries per query.

## Types of Sparse Patterns

### 1. Local Window Attention

Tokens attend only to tokens within a fixed window. This captures local patterns effectively but loses global context.

```
Complexity: O(n · w) where w = window size
```

### 2. Strided Attention

Attention follows fixed strides, similar to convolution kernels. Good for periodic structures but misses irregular dependencies.

### 3. Global Tokens

Certain tokens (like [CLS] or special sentinel tokens) attend to all others. These serve as information aggregation points.

### 4. Random Attention

Each query attends to a random subset of keys. Ensures connectivity across the sequence.

## Trade-offs

**What sparse attention gains**:
- Memory reduction by 5-20x for typical configurations
- Enables processing of sequences 10-50x longer
- Lower computational cost per forward pass

**What it sacrifices**:
- Some long-range dependencies may be missed
- Local patterns may dominate over global reasoning
- Inductive bias may not match all tasks

## Empirical Results

In experiments on Long Range Arena benchmarks:
- Sparse methods achieve within 2-5% of full attention on most tasks
- BigBird (combining window + global + random) matches full attention on genomics tasks
- Local attention alone degrades significantly on tasks requiring cross-document reasoning

![benchmark chart](https://blog.research.google/assets/benchmark_sparse.png)

## Selecting the Right Pattern

Choice depends on task characteristics:
- **Code**: Local + global (function-level structure)
- **Genomics**: Global + random (long-range dependencies)
- **Conversational**: Local + global (topic shifts)
- **Summarization**: Local + random (content selection)

## Open Questions

- Can learned sparse patterns outperform hand-designed ones?
- How does sparsity interact with quantization and pruning?
- Is there a theoretical connection between sparsity and robustness?

## Sources

- [BigBird Paper](https://arxiv.org/abs/2007.14062)
- [Longformer Paper](https://arxiv.org/abs/2004.05150)
- [Google Research Blog](https://blog.research.google/2023/03/)
