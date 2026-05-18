---
source: https://lena-voita.github.io/posts/annotated_transformers/attention.html
canonical_url: https://lena-voita.github.io/posts/annotated_transformers/attention.html
title: "Attention Mechanisms in Transformers"
tags: [transformers, attention, deep-learning, nlp]
author: Lena Voita
saved: 2026-05-10T14:23:00+00:00
type: article
rating: 9
vaultmind: false
---

# Attention Mechanisms in Transformers

## Overview

The transformer architecture relies entirely on **self-attention** to capture dependencies. Unlike RNNs, attention mechanisms allow every token to attend to every other token in the sequence, enabling parallel computation and long-range dependencies.

The core operation is:

```
Attention(Q, K, V) = softmax(QK^T / √d_k) V
```

Where Q (query), K (keys), and V (values) are projections of the input. The scaling factor `√d_k` prevents vanishing gradients in large dimension spaces.

## Multi-Head Attention

Rather than performing a single attention function, transformers project Q, K, V into `h` different subspaces. Each head learns different aspects:

- Head 1: Syntactic relationships
- Head 2: Semantic dependencies
- Head 3: Coreference patterns

This allows the model to jointly attend to information from different representation subspaces.

## Scaled Dot-Product Attention

The computational complexity is O(n² · d) for sequence length n and dimension d. For long sequences, this becomes prohibitively expensive. Various improvements like Sparse Attention, Linformer, and Performer have been proposed to reduce this complexity.

![Architecture diagram](https://lena-voita.github.io/assets/attention/attention_equation.png)

## Connection to Key-Value Memory

The attention mechanism can be interpreted as a key-value memory lookup. Each key is associated with a value, and the attention weights determine how much "memory" each key contributes to the output.

## Practical Considerations

When implementing attention:
1. Watch for NaN values — scale appropriately
2. Use masking for variable-length sequences
3. Consider flash attention for memory efficiency

## Sources

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [Lena Voita's Illustrated Guide](https://lena-voita.github.io/posts/annotated_transformers/)
