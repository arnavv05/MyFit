"""Evaluation module for Myfitness recommender systems.

Implements standard ranking and top-K metrics:
- Precision@K
- Recall@K
- NDCG@K (Normalized Discounted Cumulative Gain)
- Time-based train/test split logic
"""

import math

import pandas as pd


def compute_precision_at_k(
    recommended_ids: list[str], ground_truth_ids: set[str], k: int
) -> float:
    """Compute Precision@K: proportion of recommended items in top-K that are relevant."""
    if k <= 0 or not ground_truth_ids:
        return 0.0
    top_k = recommended_ids[:k]
    hits = sum(1 for item in top_k if item in ground_truth_ids)
    return float(hits / k)


def compute_recall_at_k(
    recommended_ids: list[str], ground_truth_ids: set[str], k: int
) -> float:
    """Compute Recall@K: proportion of relevant items captured in top-K recommendations."""
    if not ground_truth_ids or k <= 0:
        return 0.0
    top_k = recommended_ids[:k]
    hits = sum(1 for item in top_k if item in ground_truth_ids)
    return float(hits / len(ground_truth_ids))


def compute_ndcg_at_k(
    recommended_ids: list[str], ground_truth_ids: set[str], k: int
) -> float:
    """Compute Normalized Discounted Cumulative Gain at K (NDCG@K)."""
    if not ground_truth_ids or k <= 0:
        return 0.0

    top_k = recommended_ids[:k]
    dcg = 0.0
    for i, item_id in enumerate(top_k):
        if item_id in ground_truth_ids:
            # Discount factor: log2(rank + 1) where rank is 1-indexed (i + 1) -> log2(i + 2)
            dcg += 1.0 / math.log2(i + 2)

    # Ideal DCG (all hits at the very top positions)
    ideal_hits = min(k, len(ground_truth_ids))
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))

    if idcg == 0.0:
        return 0.0
    return float(dcg / idcg)


def time_based_train_test_split(
    interactions_df: pd.DataFrame,
    train_ratio: float = 0.80,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split interactions chronologically by timestamp (e.g. 80% train, 20% test).

    Ensures the model trains strictly on past behavior and tests on future behavior.
    """
    if interactions_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df_sorted = interactions_df.sort_values("timestamp").reset_index(drop=True)
    split_idx = int(len(df_sorted) * train_ratio)
    train_df = df_sorted.iloc[:split_idx].copy()
    test_df = df_sorted.iloc[split_idx:].copy()

    return train_df, test_df
