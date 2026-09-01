"""Generate the student directory tables in both README files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
STUDENTS_DIR = ROOT / "students"
START_MARKER = "<!-- START_STUDENTS_LIST -->"
END_MARKER = "<!-- END_STUDENTS_LIST -->"


def markdown_text(value: object) -> str:
    """Escape values that could break a Markdown table."""
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def profile_link(url: str) -> str:
    parsed = urlparse(url)
    username = parsed.path.strip("/").split("/")[0] or url
    return f"[@{markdown_text(username)}]({url})"


def website_link(url: str) -> str:
    label = re.sub(r"^https?://", "", url).rstrip("/") or url
    return f"[{markdown_text(label)}]({url})"


def load_students() -> list[dict[str, object]]:
    students = []
    for path in sorted(STUDENTS_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as file:
            student = json.load(file)
        if not isinstance(student, dict):
            raise ValueError(f"{path} must contain a JSON object")
        if not str(student.get("name", "")).strip():
            raise ValueError(f"{path} is missing a name")
        students.append(student)
    return sorted(students, key=lambda student: str(student["name"]).casefold())


def table(students: list[dict[str, object]], bengali: bool = False) -> str:
    if bengali:
        header = "| নাম | ব্যাচ | বিভাগ | Portfolio / Website | GitHub | প্রধান দক্ষতা |"
    else:
        header = "| Name | Batch | Department | Portfolio / Website | GitHub | Primary Skills |"
    separator = "| :--- | :---: | :---: | :---: | :---: | :--- |"
    rows = [header, separator]

    for student in students:
        skills = student.get("skills", [])
        if not isinstance(skills, list):
            skills = [skills]
        skill_text = ", ".join(markdown_text(skill) for skill in skills)
        github_url = str(student.get("githubUrl", "")).strip()
        portfolio_url = str(student.get("portfolioUrl", "")).strip()
        rows.append(
            "| {name} | {batch} | {department} | {portfolio} | {github} | {skills} |".format(
                name=f"**{markdown_text(student['name'])}**",
                batch=markdown_text(student.get("batch", "")),
                department=markdown_text(student.get("department", "")),
                portfolio=website_link(portfolio_url),
                github=profile_link(github_url),
                skills=skill_text,
            )
        )
    return "\n".join(rows)


def replace_table(readme: Path, generated_table: str) -> None:
    content = readme.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        re.DOTALL,
    )
    replacement = f"{START_MARKER}\n{generated_table}\n{END_MARKER}"
    updated, replacements = pattern.subn(replacement, content, count=1)
    if replacements != 1:
        raise ValueError(f"Expected one student-list marker pair in {readme}")
    readme.write_text(updated, encoding="utf-8")


def main() -> None:
    students = load_students()
    replace_table(ROOT / "README.md", table(students))
    replace_table(ROOT / "README.bn.md", table(students, bengali=True))


if __name__ == "__main__":
    main()
