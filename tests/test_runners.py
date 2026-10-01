"""Execute copied runners against synthetic subprocesses; never run science."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ("run_baselines.py", "runs/m0-baseline/live.json", [
        "pathway-score-st002081", "pathway-score-st002081-structural",
        "pathway-score-st000818-replication", "pathway-score-ccle",
        "pathway-score-st002081-structural-null-sensitivity",
        "pathway-score-ccle-null-ensemble", "pathway-score-ccle-property-matched-null",
    ]),
    ("run_remaining_baselines.py", "runs/m0-remaining/live.json", [
        "pathway-score-human-sensitivity", "pathway-score-human-graph-mixing",
        "pathway-score-ccle-sensitivity", "pathway-score-ccle-reaction-cluster",
        "pathway-score-mapping-supplement", "pathway-score-publication-figures",
        "factorized-pathway-publication",
    ]),
    ("run_human_grid.py", "runs/m2-human-live.json", [
        "m2-human-r2-st002081-primary", "m2-human-r2-st000818-primary",
        "m2-human-r2-st002081-missingness", "m2-human-r2-st000818-missingness",
        "m2-human-r2-st002081-resolution", "m2-human-r2-st000818-resolution",
    ]),
]

STUB = '''import os
from pathlib import Path
import signal
import sys

if "--dataset" in sys.argv:
    dataset = sys.argv[sys.argv.index("--dataset") + 1]
    mode = sys.argv[sys.argv.index("--mode") + 1]
    stage = f"m2-human-r2-{dataset}-{mode}"
elif "--output" in sys.argv:
    stage = Path(sys.argv[sys.argv.index("--output") + 1]).name
else:
    stage = __name__.rsplit(".", 1)[-1].replace("_", "-")
    # Python -m uses __main__; the file stem identifies the synthetic module.
    stage = Path(__file__).stem.replace("_", "-")
with Path(os.environ["PAPER1_TEST_EVENTS"]).open("a") as handle:
    handle.write(stage + "\\n")
print("synthetic child: " + stage, flush=True)
if stage == os.environ.get("PAPER1_TEST_FAIL_STAGE"):
    if os.environ["PAPER1_TEST_FAILURE"] == "signal":
        os.kill(os.getpid(), signal.SIGTERM)
    sys.exit(23)
output = Path.cwd() / "artifacts" / stage
output.mkdir(parents=True, exist_ok=True)
(output / "result.csv").write_text("score\\n1\\n")
'''


@pytest.mark.parametrize("runner,live_relative,stages", CASES,
                         ids=[case[0] for case in CASES])
@pytest.mark.parametrize("failure", [None, "exit", "signal"],
                         ids=["success", "child-exit-23", "child-sigterm"])
def test_runner_exit_and_durable_state(tmp_path, runner, live_relative, stages, failure):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copyfile(ROOT / "scripts" / runner, scripts / runner)
    (tmp_path / "receipts").mkdir()
    (tmp_path / "runs").mkdir()
    work = tmp_path / "work/release"
    config = work / "config"
    config.mkdir(parents=True)
    for name in ["pathway-score-human-sensitivity", "pathway-score-ccle-sensitivity"]:
        (config / (name + ".yaml")).write_text("parallel_jobs: 10\n")
    package = work / "genotype_gated_metabolism"
    modules = package / "pipelines"
    modules.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (modules / "__init__.py").write_text("")
    (scripts / "human_extension.py").write_text(STUB)
    output_sha = hashlib.sha256(b"score\n1\n").hexdigest()
    for stage in stages:
        module = stage.replace("-", "_")
        if stage == "pathway-score-ccle-property-matched-null":
            module = "pathway_score_ccle_null_ensemble"
        (modules / (module + ".py")).write_text(STUB)
        frozen = tmp_path / "inputs/central-package/reproducible-release/artifacts" / stage
        frozen.mkdir(parents=True)
        (frozen / "manifest.json").write_text(json.dumps({"output_sha256": {"result.csv": output_sha}}))

    events = tmp_path / "events.txt"
    env = os.environ.copy()
    env["PAPER1_TEST_EVENTS"] = str(events)
    env.pop("PAPER1_TEST_FAIL_STAGE", None)
    env.pop("PAPER1_TEST_FAILURE", None)
    if failure:
        env.update(PAPER1_TEST_FAIL_STAGE=stages[1], PAPER1_TEST_FAILURE=failure)
    result = subprocess.run([sys.executable, str(scripts / runner)], cwd=tmp_path,
                            env=env, capture_output=True, text=True, timeout=30)
    expected_exit = 0 if failure is None else 143 if failure == "signal" else 23
    assert result.returncode == expected_exit, (result.stdout, result.stderr)
    expected_stages = stages if failure is None else stages[:2]
    assert events.read_text().splitlines() == expected_stages
    final = json.loads((tmp_path / live_relative).read_text())
    assert final["state"] == ("finished" if failure is None else "failed")
    assert final["exit_code"] == expected_exit
    key = "completed" if runner == "run_human_grid.py" else "results"
    records = final[key]
    stage_key = "stage" if runner == "run_human_grid.py" else "artifact"
    assert [record[stage_key] for record in records] == expected_stages
    expected_child = -15 if failure == "signal" else 23 if failure else 0
    assert [record["exit_code"] for record in records] == [0] * (len(records) - 1) + [expected_child]
    if failure:
        assert final["failed_stage"] == stages[1]
    else:
        assert "failed_stage" not in final
    if runner != "run_human_grid.py":
        durable = (tmp_path / live_relative).with_name("results.json")
        assert json.loads(durable.read_text()) == records
        assert all(entry["byte_identical"] for entry in records[0]["comparisons"])
    logs = tmp_path / "receipts" if runner == "run_human_grid.py" else (tmp_path / live_relative).parent
    for stage in expected_stages:
        assert (logs / (stage + ".log")).read_text() == "synthetic child: " + stage + "\n"
    for stage in stages[len(expected_stages):]:
        assert not (logs / (stage + ".log")).exists()
