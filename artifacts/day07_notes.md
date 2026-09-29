# Day 7: Embedding experiment notes

Model: embeddinggemma. Vector length: 768.

## What I tested
5 questions, each written to match a specific document, plus one unrelated
question ("What is the capital of France?") as a baseline for "no real match".

## What I found
(Fill in your actual numbers from the run above)
- Related queries found their expected document in the top 5: __/5
- Average top score for related queries: ____
- Top score for the unrelated query: ____

## What this tells me
(Write 2-3 sentences: did the gap between related and unrelated scores feel
large enough to trust? Which query scored lowest, and can you guess why?)

## Bug found and fixed
The first version of embed_kb.py took chunks[:20], which happened to grab
100% of KB-ACCOUNT and KB-TROUBLESHOOT and 0% of the other three documents,
because chunks were ordered alphabetically by filename. This explained the
3 failed queries exactly (KB-RETURNS, KB-SHIPPING, KB-WARRANTY were all
missing from the embedded set). Fixed by round-robin sampling across all
documents. Re-ran with even coverage: __/5 hits, average score ____.
