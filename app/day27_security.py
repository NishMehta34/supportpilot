"""Day 27 strict tenant-bound retrieval adapter for new integrations.

Wrap any RAG callback before giving it to SupportToolbox. This fails closed
if a result lacks tenant metadata, so legacy unscoped chunks are not trusted.
"""
import math

class RetrievalBoundaryError(RuntimeError):
    pass

def tenant_checked_retrieval(retrieve_fn):
    def checked(query, tenant_id, limit):
        raw = retrieve_fn(query, tenant_id, limit)
        if not isinstance(raw, (list, tuple)):
            raise RetrievalBoundaryError('invalid retrieval result')
        output = []
        for chunk in raw[:50]:
            if not isinstance(chunk, dict) or chunk.get('tenant_id') != tenant_id:
                raise RetrievalBoundaryError('unscoped retrieval result')
            try:
                score = float(chunk['score'])
                if not math.isfinite(score):
                    raise ValueError('invalid score')
                if not all(isinstance(chunk.get(k), str) for k in ('doc_id','section','content')):
                    raise ValueError('invalid content')
            except (ValueError, TypeError, KeyError):
                raise RetrievalBoundaryError('invalid retrieval chunk') from None
            output.append({**chunk, 'score': score})
        return output[:limit]
    return checked
