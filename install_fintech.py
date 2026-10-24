import os
import shutil
from pathlib import Path
import yaml

repo_root = Path(r"c:\Users\amoni\OneDrive\Desktop\DayTrade\claude-fintech-skills")
claude_skills = Path(r"c:\Users\amoni\OneDrive\Desktop\DayTrade\.claude\skills")
antigravity_skills = Path(r"C:\Users\amoni\.gemini\config\skills")
claude_commands = Path(r"c:\Users\amoni\OneDrive\Desktop\DayTrade\.claude\commands")
user_claude_commands = Path(os.path.expanduser("~/.claude/commands"))

claude_skills.mkdir(parents=True, exist_ok=True)
antigravity_skills.mkdir(parents=True, exist_ok=True)
claude_commands.mkdir(parents=True, exist_ok=True)
user_claude_commands.mkdir(parents=True, exist_ok=True)

installed = []

for sub in ["trading", "infrastructure", "network", "security", "monitoring", "telephony", "frontend", "data"]:
    sub_dir = repo_root / sub
    if not sub_dir.exists():
        continue
    for md_file in sub_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        if not content.startswith("---"):
            continue
        
        name = md_file.stem
        
        # 1. Install as SKILL.md in project .claude/skills/<name>/SKILL.md
        p_skill = claude_skills / name
        p_skill.mkdir(parents=True, exist_ok=True)
        (p_skill / "SKILL.md").write_text(content, encoding="utf-8")
        
        # 2. Install as SKILL.md in global Antigravity config
        ag_skill = antigravity_skills / name
        ag_skill.mkdir(parents=True, exist_ok=True)
        (ag_skill / "SKILL.md").write_text(content, encoding="utf-8")
        
        # 3. Install in .claude/commands/ and ~/.claude/commands/
        (claude_commands / f"{name}.md").write_text(content, encoding="utf-8")
        (user_claude_commands / f"{name}.md").write_text(content, encoding="utf-8")
        
        installed.append({"name": name, "category": sub})

print(f"Successfully installed {len(installed)} FinTech skills across all platforms!")
for item in installed:
    print(f"  + [{item['category']}] {item['name']}")
