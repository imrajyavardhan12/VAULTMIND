---
title: "Attention Mechanisms"
vaultmind: true
kind: concept
sources:
  - https://lena-voita.github.io/posts/annotated_transformers/attention.html
---

# Attention Mechanisms

## Overview

Attention mechanisms are the foundational operation underlying modern transformer models. They allow every token in a sequence to dynamically weight its relationship to every other token, enabling the model to capture long-range dependencies without sequential processing.

## Key Ideas

- **Scaled Dot-Product**: The core attention formula normalizes by √d_k to prevent gradient vanishing in high dimensions
- **Multi-Head**: Multiple attention heads learn different types of relationships (syntactic, semantic, coreference) in parallel
- **Key-Value Interpretation**: Attention can be viewed as a soft key-value memory lookup where keys determine relevance weights

## Architecture

The standard attention mechanism computes:

```
Attention(Q, K, V) = softmax(QK^T / √d_k) V
```

Multi-head attention projects Q, K, V into h subspaces, applies attention separately, then concatenates and projects the results.

## Complexity Considerations

Standard attention is O(n² · d) in sequence length n and model dimension d. This makes processing very long documents expensive. Various efficiency approaches have been explored:

- **Sparse Attention**: Only attend to a subset of positions (BigBird, Longformer)
- **Linear Attention**: Kernel-based approximations (Performer, Linformer)
- **Flash Attention**: IO-aware exact attention that reduces memory reads/writes

## Connections

- [[transformers]] — attention is the core building block
- [[sparse-attention]] — efficiency variants
- [[rlhf-alignment]] — attention patterns in language model training

## Open Questions

- Can sparse attention patterns be learned end-to-end rather than hand-designed?
- How does attention sparsity interact with model scale?
- What do different attention heads learn and can we guide their specialization?

## Sources

- [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- [Lena Voita's Illustrated Guide](https://lena-voita.github.io/posts/annotated_transformers/)
- [BigBird Paper](https://arxiv.org/abs/2007.14062)
