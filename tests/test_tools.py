import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import specialists  # noqa: F401
import config
from agent import tools as T

MIN_TOOLS = 8


def test_enough_tools_registered():
    assert len(T.TOOLS) >= MIN_TOOLS


def test_every_tool_has_a_kind_and_schema():
    for name, t in T.TOOLS.items():
        assert t["kind"] in {"read", "analyze", "model", "write", "act", "never"}, name
        assert t["parameters"]["type"] == "object", name


def test_summarize_home_member_runs():
    r = T.call("summarize_member", {"member": config.HOME_MEMBER})
    assert r["rows"] > 0 and 0 <= r["outcome_rate"] <= 1


def test_model_card_facts_available():
    r = T.call("model_card_facts", {})
    assert "neutral_test_accuracy" in r and r["gate_decision"] == "PASS"

def test_top_segments_consortium_wide_runs():
    r = T.call(
        "top_segments_consortium_wide",
        {"segment": "course_level"}
    )

    assert r["segment"] == "course_level"
    assert "rates" in r
    assert "lower_division" in r["rates"]
    assert all("outcome_rate" in value for value in r["rates"].values())


def test_segment_driver_runs():
    r = T.call(
        "segment_driver",
        {
            "member_a": "Marketing",
            "member_b": "Accounting",
            "segment": "course_level"
        }
    )

    assert r["member_a"] == "Marketing"
    assert r["member_b"] == "Accounting"
    assert r["segment"] == "course_level"
    assert len(r["differences"]) > 0

    first_difference = r["differences"][0]
    assert "segment_value" in first_difference
    assert "difference" in first_difference
