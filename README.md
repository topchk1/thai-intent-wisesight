# Thai social media intent classification

Data and code for *Intent Classification of Thai Social Media Text Using Deep Learning Models and Large Language Model Annotation* (NLPIR 2026).

Labels for 26,243 Wisesight Sentiment posts were produced by GPT-5-mini (`gpt-5-mini-2025-08-07`). They are LLM-derived reference labels, not ground truth.

## Files

| Path | Content |
|---|---|
| `prompt/` | annotation codebook (Thai, with English translation) and the system prompt used for annotation, including the 29 examples |
| `filtering/` | advertisement filter and the ids of the 460 removed posts |
| `data/reference_labels.csv` | `id`, `split`, `label`, `text` |
| `data/human_labels/` | human audit labels |
| `modelling/`, `baselines/` | training code (BiLSTM, mBERT, WangchanBERTa, TF-IDF + SVM) |
| `config.yaml` | training settings |

`id` is the row position in the Wisesight Sentiment train, validation and test files read in that order, before filtering. The prompt is published as used; its 29 examples are not balanced across classes. Three posts flagged by the filter script (ids 20275, 21388, 26110) are not advertisements and were kept.

## Training

```bash
pip install -r requirements.txt
python -m modelling.train                 # default setting
python -m modelling.train --stage tune    # search on the validation split
python -m modelling.train --stage tuned   # best setting per model
python baselines/tfidf_svm.py
```

## License

Code: MIT. Labels, codebook and prompt: CC0 1.0. Post texts are from the Wisesight Sentiment corpus (CC0 1.0); please also cite it:

```bibtex
@software{wisesight_sentiment,
  author    = {Suriyawongkul, Arthit and Chuangsuwanich, Ekapol and Chormai, Pattarawat and Chantarapratin, Nitchakarn and Prasertsom, Ponrawee and Sawatphol, Jitkapat and Yamada, Nozomi and Rutherford, Attapol and Polpanumas, Charin and Udomcharoenchaikit, Can},
  title     = {PyThaiNLP/wisesight-sentiment: Wisesight Sentiment Corpus with word tokenization label},
  version   = {1.1},
  publisher = {Zenodo},
  year      = {2024},
  doi       = {10.5281/zenodo.3457446}
}
```

## Citation

```bibtex
@inproceedings{changsorn2026intent,
  title     = {Intent Classification of Thai Social Media Text Using Deep Learning Models and Large Language Model Annotation},
  author    = {Changsorn, Kritsaya and Jareevongpiboon, Wirat},
  booktitle = {Proceedings of the 10th International Conference on Natural Language Processing and Information Retrieval (NLPIR 2026)},
  series    = {Lecture Notes in Networks and Systems},
  publisher = {Springer},
  year      = {2026}
}
```
