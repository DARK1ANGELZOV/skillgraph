from pathlib import Path

import yaml


class PromptRegistry:
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir

    def load_template(self, prompt_file: str, version: str | None = None) -> str:
        path = self.prompts_dir / prompt_file
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        default_version = data["default_version"]
        chosen_version = version or default_version

        variants = data["versions"]
        if chosen_version not in variants:
            raise ValueError(f"Prompt version {chosen_version} missing in {prompt_file}")

        return variants[chosen_version]["template"]
