"""
DESCRIPTIVE SPECIALIST: what happened. Aggregates only; a member's rows never leave its file.

Working tools: summarize_member, segment_breakdown, trend_by_month.
TODO for your team: at least one more (for example compare_month_over_month, top_segments_consortium_wide).
"""
from collections import Counter, defaultdict

from agent import tools as T
from . import _data as D
import config  # noqa: E402  (MIN_CELL_SIZE)


def _rates(tot, pos):
    """Outcome rate per group, highest first. Groups smaller than config.MIN_CELL_SIZE are suppressed (no rate)."""
    n_min = config.MIN_CELL_SIZE
    shown = sorted((k for k in tot if tot[k] >= n_min), key=lambda k: -pos[k] / tot[k])
    out = {k: {"rows": tot[k], "outcome_rate": round(pos[k] / tot[k], 3)} for k in shown}
    out.update({k: {"rows": f"<{n_min}", "outcome_rate": None, "suppressed": True} for k in tot if tot[k] < n_min})
    return out


@T.tool("summarize_member", "Row count, outcome rate and segment mix for one member. Aggregate only.",
        T.obj_schema({"member": ("string", "member name exactly as in the data card")}), kind="read")
def summarize_member(member):
    c = D.member(member)
    lab = D.label()
    out = {"member": member, "rows": c.n, "outcome_rate": round(float(c.y_train.mean()), 3), "segments": {}}
    for seg in D.world().segments:
        cnt = Counter(r[seg] for r in c.rows)
        out["segments"][seg] = {k: v for k, v in cnt.most_common()}
    return out


@T.tool("segment_breakdown", "Outcome rate by one segment column for one member (for example by ward or by claim_type).",
        T.obj_schema({"member": ("string", "member name"), "segment": ("string", "a segment column from the data card")}), kind="read")
def segment_breakdown(member, segment):
    c = D.member(member)
    if segment not in D.world().segments:
        return {"error": f"{segment} is not a segment column; choose from {D.world().segments}"}
    lab = D.label()
    tot, pos = Counter(), Counter()
    for r in c.rows:
        tot[r[segment]] += 1
        pos[r[segment]] += int(r[lab])
    return {"member": member, "segment": segment, "rates": _rates(tot, pos), "min_cell_size": config.MIN_CELL_SIZE}


@T.tool("trend_by_month", "Outcome rate by month (1 to 12) for one member.",
        T.obj_schema({"member": ("string", "member name")}), kind="read")
def trend_by_month(member):
    c = D.member(member)
    lab = D.label()
    tot, pos = defaultdict(int), defaultdict(int)
    for r in c.rows:
        m = int(r["month"])
        tot[m] += 1
        pos[m] += int(r[lab])
    n_min = config.MIN_CELL_SIZE
    rates = {m: (round(pos[m] / tot[m], 3) if tot[m] >= n_min else None) for m in sorted(tot)}
    shown = {m: v for m, v in rates.items() if v is not None}
    suppressed = [m for m, v in rates.items() if v is None]
    if not shown:
        return {"member": member, "rate_by_month": rates, "suppressed_months": suppressed, "min_cell_size": n_min,
                "note": f"every month has fewer than {n_min} rows; no monthly rate can be reported"}
    hi = max(shown, key=shown.get)
    lo = min(shown, key=shown.get)
    return {"member": member, "rate_by_month": rates, "highest_month": hi, "lowest_month": lo,
            "suppressed_months": suppressed, "min_cell_size": n_min}
@T.tool(
    "top_segments_consortium_wide",
    "Compare outcome rates across all consortium members for one segment.",
    T.obj_schema({
        "segment": (
            "string",
            "segment column such as course_level, modality, or month"
        )
    }),
    kind="read"
)
def top_segments_consortium_wide(segment):
    if segment not in D.world().segments:
        return {
            "error": (
                f"{segment} is not a segment column; "
                f"choose from {D.world().segments}"
            )
        }

    label = D.label()
    total = Counter()
    positive = Counter()

    for client in D.world().clients:
        for row in client.rows:
            value = row[segment]
            total[value] += 1
            positive[value] += int(row[label])

    rates = _rates(total, positive)

    return {
        "segment": segment,
        "rates": rates,
        "reading": (
            "These are aggregate rates across all departments; "
            "no individual student records are returned."
        )
    }
@T.tool(
    "segment_driver",
    "Compare outcome rates by segment between two members.",
    T.obj_schema({
        "member_a": ("string", "first member"),
        "member_b": ("string", "second member"),
        "segment": (
            "string",
            "segment column such as course_level or modality"
        )
    }, required=["member_a", "member_b", "segment"]),
    kind="analyze"
)
def segment_driver(member_a, member_b, segment):
    if segment not in D.world().segments:
        return {
            "error": (
                f"{segment} is not a segment column; "
                f"choose from {D.world().segments}"
            )
        }

    label = D.label()

    def rates_for(member):
        client = D.member(member)
        totals = {}
        positives = {}

        for row in client.rows:
            value = row[segment]
            totals[value] = totals.get(value, 0) + 1
            positives[value] = positives.get(value, 0) + int(row[label])

        return {k: v for k, v in _rates(totals, positives).items() if not v.get("suppressed")}

    rates_a = rates_for(member_a)
    rates_b = rates_for(member_b)

    all_values = set(rates_a) | set(rates_b)
    differences = []

    for value in all_values:
        rate_a = rates_a.get(value, {}).get("outcome_rate")
        rate_b = rates_b.get(value, {}).get("outcome_rate")

        if rate_a is not None and rate_b is not None:
            differences.append({
                "segment_value": value,
                "member_a_rate": rate_a,
                "member_b_rate": rate_b,
                "difference": round(rate_a - rate_b, 3)
            })

    differences.sort(
        key=lambda item: abs(item["difference"]),
        reverse=True
    )

    return {
        "member_a": member_a,
        "member_b": member_b,
        "segment": segment,
        "differences": differences,
        "reading": (
            "The segment values with the largest absolute differences "
            "show where the members differ most."
        )
    }