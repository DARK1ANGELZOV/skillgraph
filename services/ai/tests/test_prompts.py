from pathlib import Path

from skillgraph_ai.prompts import PromptRegistry


def test_prompt_registry_reads_versioned_template():
    prompts_dir = Path("services/ai/prompts")
    registry = PromptRegistry(prompts_dir)

    template = registry.load_template("interview.yaml", "v1")
    assert "Generate {count}" in template

    template_v2 = registry.load_template("interview.yaml", "v2")
    assert "Role-specific" in template_v2 or "role-specific" in template_v2
