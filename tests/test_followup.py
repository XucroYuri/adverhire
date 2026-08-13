from adverhire.followup import classify_answer, next_followup
from adverhire.llm import ModelRole, MockLLM
from adverhire.models import ImpactedTrap, Claim

TRAP = ImpactedTrap(Claim("优化缓存 QPS+50%", ["redis"], 50.0, "resume"),
                    wrong_preset="改成1800", question="从200怎么调到1800的？",
                    discriminators=["纠正", "其实"])

def test_classify_corrected_hits_discriminator():
    assert classify_answer("其实不是，我们从200调到的是1200", TRAP) == "corrected"

def test_classify_vague_when_short_or_forgetful():
    assert classify_answer("嗯…" * 3, TRAP) == "vague"          # 太短
    assert classify_answer("记不清那段细节了", TRAP) == "vague"   # 记不清

def test_classify_defaults_to_echoed():
    assert classify_answer("当时我们做了业务优化和性能提升，整体效果好很多", TRAP) == "echoed"

def test_next_followup_hits_corrected_marks_terminal_layer():
    mock = MockLLM(responses={ModelRole.PRO: ["当时你是怎么发现这个问题的？"]})
    fu = next_followup(mock, TRAP, "其实不是，这个改动不是我做的", depth=1)
    assert fu.branch == "corrected" and fu.discriminator_hit is True
    assert fu.depth == 2 and "发现" in fu.question
