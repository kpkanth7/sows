"""Phase 3.8: real influencer trust decay.

Replaces the previous stub (naive 50% word-overlap matcher) with:

  1. LLM-validated claims — for each unresolved claim aged >= 7d, ask the LLM
     "did tier-1/2 news in the [made_at, made_at+VALIDATION_WINDOW] window
     CONFIRM, REFUTE, or stay AMBIGUOUS about this claim?"
     Batched up to 6 claims per LLM call to amortize quota.

  2. Per-influencer trust update from validation outcomes
       CONFIRM   -> +0.025
       REFUTE    -> -0.040
       AMBIGUOUS -> skip (no signal either way)
     Clamped to [0.05, 0.60] (schema bound).

  3. Time decay every run — every influencer's trust pulls 1% toward the 0.20
     baseline. Silent influencers drift home; high-trust requires fresh wins
     to maintain status.

  4. Quota-gated. If the LLM provider chain is exhausted, validation is
     skipped but decay still runs (so the trust panel keeps moving).
"""
import json
import logging
from datetime import datetime, timedelta, timezone

from db import get_client, record_health
from llm import generate_llm_content, strip_json_fence, has_llm_capacity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# How old a claim must be before we judge it (gives news time to surface).
VALIDATION_AGE_DAYS = 7
# How wide a news window around the claim we feed the LLM.
VALIDATION_WINDOW_DAYS = 10
# Trust deltas per outcome.
DELTA_CONFIRM = 0.025
DELTA_REFUTE = -0.040
# Clamp.
TRUST_MIN, TRUST_MAX = 0.05, 0.60
BASELINE = 0.20
DECAY_PULL = 0.01  # 1% pull toward baseline per run
# Batching.
CLAIMS_PER_PROMPT = 6
MAX_CLAIMS_PER_RUN = 60


def _decay_all(sb):
    """Pull every influencer's trust 1% toward BASELINE. Cheap, deterministic."""
    res = sb.table('influencers').select('id, trust_score').execute()
    rows = res.data or []
    for r in rows:
        cur = float(r.get('trust_score') or BASELINE)
        new = cur + (BASELINE - cur) * DECAY_PULL
        new = max(TRUST_MIN, min(TRUST_MAX, new))
        if abs(new - cur) > 1e-4:
            sb.table('influencers').update({'trust_score': round(new, 3)}).eq('id', r['id']).execute()
    logger.info(f"decay: pulled {len(rows)} influencers toward {BASELINE}")


def _gather_evidence(sb, claim):
    """News evidence within [made_at, made_at+VALIDATION_WINDOW] for the entity, tier 1/2 only."""
    start = claim['made_at']
    end_dt = datetime.fromisoformat(start.replace('Z', '+00:00')) + timedelta(days=VALIDATION_WINDOW_DAYS)
    res = (
        sb.table('news_items')
          .select('title, summary, source_credibility_tier')
          .contains('entity_names', [claim.get('entity_name')])
          .in_('source_credibility_tier', [1, 2])
          .gte('published_at', start)
          .lte('published_at', end_dt.isoformat())
          .limit(8)
          .execute()
    )
    return res.data or []


def _validate_batch(sb, batch):
    """LLM-validate a batch of claims. Returns dict id -> 'CONFIRM'|'REFUTE'|'AMBIGUOUS'."""
    lines = [
        "You judge whether tier-1/2 news evidence CONFIRMS or REFUTES each claim.",
        "Reply with strict JSON: {\"<claim_id>\": \"CONFIRM|REFUTE|AMBIGUOUS\", ...}",
        "Use AMBIGUOUS when evidence is mixed, irrelevant, or absent. No prose.\n",
    ]
    for c in batch:
        evidence = _gather_evidence(sb, c)
        lines.append(f"CLAIM_ID: {c['id']}")
        lines.append(f"ENTITY: {c.get('entity_name')}")
        lines.append(f"CLAIM: {c.get('claim_text')}")
        lines.append("EVIDENCE:")
        if not evidence:
            lines.append("  (no tier-1/2 news in window)")
        else:
            for e in evidence:
                tier = e.get('source_credibility_tier')
                lines.append(f"  [T{tier}] {e.get('title')} :: {(e.get('summary') or '')[:140]}")
        lines.append("")
    prompt = "\n".join(lines)
    try:
        text = generate_llm_content(prompt, sb)
        parsed = json.loads(strip_json_fence(text))
        return {str(k): str(v).upper() for k, v in (parsed or {}).items()}
    except Exception as e:
        logger.warning(f"LLM batch validate failed: {e}")
        return {}


def _apply_outcome(sb, claim, outcome: str):
    """Update claims row + influencer counters/trust per outcome."""
    if outcome not in ('CONFIRM', 'REFUTE', 'AMBIGUOUS'):
        return
    validated = outcome == 'CONFIRM'
    if outcome != 'AMBIGUOUS':
        sb.table('claims').update({
            'validated': validated,
            'validated_at': datetime.now(timezone.utc).isoformat(),
            'validated_by': 'llm_semantic',
        }).eq('id', claim['id']).execute()
    # Resolve influencer via name first, fall back to channel_id (legacy path).
    src_name = claim.get('source_name') or ''
    inf_res = sb.table('influencers').select('id, trust_score, total_claims, correct_claims').eq('name', src_name).execute()
    if not inf_res.data:
        inf_res = sb.table('influencers').select('id, trust_score, total_claims, correct_claims').eq('channel_id', src_name).execute()
    if not inf_res.data:
        return
    inf = inf_res.data[0]
    trust = float(inf.get('trust_score') or BASELINE)
    if outcome == 'CONFIRM':
        trust += DELTA_CONFIRM
    elif outcome == 'REFUTE':
        trust += DELTA_REFUTE
    trust = max(TRUST_MIN, min(TRUST_MAX, trust))
    update = {'trust_score': round(trust, 3)}
    if outcome != 'AMBIGUOUS':
        update['total_claims'] = (inf.get('total_claims') or 0) + 1
        if outcome == 'CONFIRM':
            update['correct_claims'] = (inf.get('correct_claims') or 0) + 1
    sb.table('influencers').update(update).eq('id', inf['id']).execute()


def main():
    sb = get_client()

    # 1) Decay always runs — keeps the panel moving even when LLM is exhausted.
    _decay_all(sb)

    if not has_llm_capacity(sb, 1):
        logger.warning("LLM quota exhausted — skipping validation pass.")
        return

    cutoff = (datetime.now(timezone.utc) - timedelta(days=VALIDATION_AGE_DAYS)).isoformat()
    res = (
        sb.table('claims')
          .select('id, claim_text, entity_name, source_name, made_at')
          .is_('validated', 'null')
          .lte('made_at', cutoff)
          .order('made_at')
          .limit(MAX_CLAIMS_PER_RUN)
          .execute()
    )
    claims = res.data or []
    logger.info(f"validation: {len(claims)} unresolved claims aged >= {VALIDATION_AGE_DAYS}d")
    if not claims:
        return

    processed = 0
    for i in range(0, len(claims), CLAIMS_PER_PROMPT):
        if not has_llm_capacity(sb, 1):
            logger.warning("Quota tripped mid-run; stopping.")
            break
        batch = claims[i:i + CLAIMS_PER_PROMPT]
        outcomes = _validate_batch(sb, batch)
        for c in batch:
            outcome = outcomes.get(str(c['id']), 'AMBIGUOUS')
            _apply_outcome(sb, c, outcome)
            processed += 1
    logger.info(f"validation: processed {processed} claims")


if __name__ == '__main__':
    try:
        main()
        record_health(get_client(), 'update_influencer_trust', 'ok')
    except Exception as e:
        record_health(get_client(), 'update_influencer_trust', 'error', str(e))
        raise
