# MeLi Listing Scorer — Research Directives

## Objective
Train a scoring model that predicts listing quality (0-100) for Mercado Libre listings.

## Data Source
- PostgreSQL `listings` table with attribute completeness, health status, optimization history
- Optimization outcomes: did applied changes improve quality scores?

## Model Architecture
- Encoder-based model (e.g., small BERT variant or custom transformer)
- Input: tokenized title + category embedding + attribute features + price normalization
- Output: single scalar quality score (0-100)

## Training Strategy
1. Start with attribute completeness as proxy target
2. Graduate to actual quality score changes post-optimization
3. Multi-market: train shared model with site_id as feature

## Evaluation Metrics
- MAE on quality score prediction
- Ranking correlation (Spearman's rho)
- A/B: does model-scored listings lead to better optimization suggestions?

## Constraints
- Must run on single GPU (nightly batch)
- Inference must be CPU-friendly (< 50ms per listing)
- Support MLA, MLB, MLM market features
