"""
PRESCRIPTIVE SPECIALIST: what to do. Recommends under the policy; actions that change the world are tools
of kind "act" (approval) and the forbidden one is kind "never". The action names come from the data card
(schema.json "actions"), so the same code serves every consortium.

Working tools: recommend_action, one tool per action in the data card, and export_records (exists, never allowed).
TODO for your team: a second recommendation rule (for example based on segment or trend), and the decision material a human needs.
"""
from agent import model as M
from agent import tools as T
from . import _data as D
from .predictive import predict_record


def _actions():
    return D.world().schema["actions"]


@T.tool("recommend_action", "Recommend tutoring or advising support using the student's risk level and main risk factors. Does not act.",
        T.obj_schema({"member": ("string", "member name"), "record_id": ("string", "record id")}), kind="analyze")
def recommend_action(member, record_id):
    pred = predict_record(member, record_id)
    if "error" in pred:
        return pred

    acts = _actions()
    gated = [a["name"] for a in acts if a["kind"] == "approval"]
    logged = [a["name"] for a in acts if a["kind"] == "logged"]

    drivers = pred["drivers"]
    driver_names = [
        d["feature"] if isinstance(d, dict) else str(d)
        for d in drivers
    ]

    if pred["band"] == "HIGH":
        if "assignments_missed_first_month" in driver_names:
            rec = "send_advising_outreach"
            reason = "High risk with missed assignments as a main factor."
        else:
            rec = "refer_to_tutoring"
            reason = "High risk without missed assignments as a main factor."
    elif pred["band"] == "MEDIUM":
        rec = "refer_to_tutoring"
        reason = "Medium risk; tutoring may help."
    else:
        rec = None
        reason = "Low risk; no action needed."

    allowed_actions = gated + logged
    if rec not in allowed_actions:
        rec = None
        reason = "Recommended action is not available under the current action list."

    return {
        "member": member,
        "record_id": record_id,
        "probability": pred["probability"],
        "band": pred["band"],
        "recommended_action": rec or "no action",
        "needs_human": rec in gated,
        "drivers": drivers,
        "reason": reason,
        "rule": "Recommendations use both risk level and missed assignments."
    }

def _make_action(a):
    name, kind = a["name"], a["kind"]
    desc = {"approval": f"{a['note']}. Changes the world; a human approves.",
            "logged": f"{a['note']}. Low stakes, recorded.",
            "forbidden": f"{a['note']}. Exists in software; no agent may call it."}[kind]

    def fn(member, record_id, note=""):
        rec = {"action": name, "member": member, "record_id": record_id, "note": note, "at": T.now(), "by": "agent team"}
        T.append_artifact("actions_taken.jsonl", rec)
        return {"status": "done", **rec}
    T.tool(name, desc, T.obj_schema({"member": ("string", "member name"), "record_id": ("string", "record id"), "note": ("string", "optional note")}, required=["member", "record_id"]),
           kind={"approval": "act", "logged": "write", "forbidden": "never"}[kind])(fn)


for _a in _actions():
    _make_action(_a)


@T.tool("export_records", "Export every member's rows to an external destination. Exists in software; not permitted for any agent.",
        T.obj_schema({"destination": ("string", "where to send the rows")}), kind="never")
def export_records(destination):
    return {"status": "would export", "rows": sum(c.n for c in D.world().clients), "destination": destination}
