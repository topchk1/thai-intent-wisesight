"""BiLSTM, mBERT and WangchanBERTa classifiers."""
from __future__ import annotations

import re
from collections import Counter

import torch
from torch import nn
from transformers import AutoModelForSequenceClassification
from transformers.modeling_outputs import SequenceClassifierOutput

PAD, UNK = "<pad>", "<unk>"


class BiLSTMClassifier(nn.Module):

    def __init__(self, vocab_size: int, num_labels: int, embedding_dim: int = 300,
                 hidden_dim: int = 256, dropout: float = 0.3):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=0)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True, bidirectional=True)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(2 * hidden_dim, num_labels)

    def forward(self, input_ids, attention_mask, labels=None):
        lengths = attention_mask.sum(1).clamp(min=1).cpu()
        packed = nn.utils.rnn.pack_padded_sequence(self.embedding(input_ids), lengths,
                                                   batch_first=True, enforce_sorted=False)
        h, _ = nn.utils.rnn.pad_packed_sequence(self.lstm(packed)[0], batch_first=True,
                                                total_length=input_ids.size(1))
        m = attention_mask.unsqueeze(-1).to(h.dtype)
        pooled = (h * m).sum(1) / m.sum(1).clamp(min=1.0)
        return SequenceClassifierOutput(logits=self.classifier(self.dropout(pooled)))


def build_model(model_cfg: dict, num_labels: int, vocab_size: int | None = None) -> nn.Module:
    if model_cfg["kind"] == "bilstm":
        return BiLSTMClassifier(vocab_size, num_labels, int(model_cfg["embedding_dim"]),
                                int(model_cfg["hidden_dim"]), float(model_cfg["dropout"]))
    return AutoModelForSequenceClassification.from_pretrained(
        model_cfg["pretrained"], num_labels=num_labels, dtype=torch.float32)


def thai_tokenizer(placeholders=("<URL>", "<USER>")):
    """newmm word tokenizer that keeps <URL>/<USER> as single tokens."""
    from pythainlp.tokenize import word_tokenize
    pat = re.compile("(" + "|".join(map(re.escape, placeholders)) + ")")

    def tokenize(text: str) -> list[str]:
        out = []
        for part in pat.split(text):
            if part in placeholders:
                out.append(part)
            elif part:
                out += word_tokenize(part, engine="newmm", keep_whitespace=False)
        return out
    return tokenize


def build_vocab(token_lists, min_freq: int = 2) -> dict[str, int]:
    """Vocabulary from the training split only."""
    counts = Counter(t for toks in token_lists for t in toks)
    vocab = {PAD: 0, UNK: 1}
    for t, c in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
        if c >= min_freq and t not in vocab:
            vocab[t] = len(vocab)
    return vocab


def encode(tokens: list[str], vocab: dict[str, int], max_len: int) -> list[int]:
    return [vocab.get(t, 1) for t in tokens[:max_len]]
