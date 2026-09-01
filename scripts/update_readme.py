"""Generate the student directory tables in both README files."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
STUDENTS_DIR = ROOT / "students"
START_MARKER = "<!-- START_STUDENTS_LIST -->"
END_MARKER = "<!-- END_STUDENTS_LIST -->"
COUNT_MARKER = "<!-- COUNT -->"


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


def valid_url(value: object) -> str:
    url = str(value or "").strip()
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return url
    return ""


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
    grouped = {letter: [] for letter in "abcdefghijklmnopqrstuvwxyz"}
    for student in students:
        first_letter = str(student["name"]).strip()[:1].casefold()
        if first_letter in grouped:
            grouped[first_letter].append(student)

    rows = []
    for letter, letter_students in grouped.items():
        if not letter_students:
            continue
        rows.extend([f'<a name="{letter}"></a>', f"### {letter.upper()}", header, separator])
        for student in letter_students:
            skills = student.get("skills", [])
            if not isinstance(skills, list):
                skills = [skills]
            skill_text = ", ".join(markdown_text(skill) for skill in skills)
            github_url = valid_url(student.get("githubUrl"))
            portfolio_url = valid_url(student.get("portfolioUrl"))
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
        rows.append("")
    return "\n".join(rows)


def active_letters(students: list[dict[str, object]]) -> list[str]:
    return sorted(
        {
            str(student["name"]).strip()[:1].casefold()
            for student in students
            if str(student["name"]).strip()[:1].casefold() in "abcdefghijklmnopqrstuvwxyz"
        }
    )


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


def replace_count(readme: Path, count: int) -> None:
    content = readme.read_text(encoding="utf-8")
    pattern = re.compile(r"^## Current Portfolio Count:.*$", re.MULTILINE)
    replacement = f"## Current Portfolio Count: {count}"
    updated, replacements = pattern.subn(replacement, content, count=1)
    if replacements != 1:
        raise ValueError(f"Expected one portfolio count line in {readme}")
    readme.write_text(updated, encoding="utf-8")


def replace_navigation(readme: Path, letters: list[str], url: str) -> None:
    content = readme.read_text(encoding="utf-8")
    links = " | ".join(f"[{letter.upper()}](#{letter})" for letter in letters)
    navigation = f"**Jump to:** {links} | [Random Portfolio]({url})"
    updated, replacements = re.subn(
        r"^\*\*Jump to:\*\*.*$",
        navigation,
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if replacements != 1:
        raise ValueError(f"Expected one jump navigation bar in {readme}")
    readme.write_text(updated, encoding="utf-8")


def main() -> None:
    students = load_students()
    random_urls = []
    for student in students:
        portfolio_url = valid_url(student.get("portfolioUrl"))
        github_url = valid_url(student.get("githubUrl"))
        if portfolio_url or github_url:
            random_urls.append(portfolio_url or github_url)
    if random_urls:
        random_url = random.choice(random_urls)
    else:
        random_url = ""
    letters = active_letters(students)

    for readme, generated_table in (
        (ROOT / "README.md", table(students)),
        (ROOT / "README.bn.md", table(students, bengali=True)),
    ):
        replace_count(readme, len(students))
        replace_table(readme, generated_table)
        if random_url:
            replace_navigation(readme, letters, random_url)


if __name__ == "__main__":
    main()
