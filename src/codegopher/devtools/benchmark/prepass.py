"""Source-derived static inventory for chained-audit benchmark prompts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

SOURCE_EXTENSIONS = {
    ".cs",
    ".css",
    ".go",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".sql",
    ".ts",
    ".tsx",
    ".xml",
    ".yaml",
    ".yml",
}
SKIP_DIRS = {
    ".git",
    ".hg",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
}
MAX_FILE_BYTES = 256_000
MAX_MATCHES_PER_CATEGORY = 16
MAX_TOTAL_MATCHES = 128
MAX_SNIPPET_CHARS = 180
REMOVED_BASENAMES = {"readme.md", "impl_plan.md", ".vulns", "vulns.json", "scenarios.md"}


@dataclass(frozen=True)
class InventoryMatch:
    category: str
    item_id: str
    path: str
    line: int
    snippet: str


@dataclass(frozen=True)
class FocusQueueCategory:
    name: str
    items: tuple[InventoryMatch, ...]


@dataclass(frozen=True)
class StaticFocusQueue:
    categories: tuple[FocusQueueCategory, ...]

    @property
    def total_items(self) -> int:
        return sum(len(category.items) for category in self.categories)


CATEGORY_PATTERNS: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    (
        "Routes and entry points",
        (
            re.compile(r"@\s*(?:Get|Post|Put|Delete|Patch|Request)Mapping\b"),
            re.compile(r"\b(?:app|router)\.(?:get|post|put|delete|patch)\s*\("),
            re.compile(r"@\s*(?:app|bp)\.route\s*\("),
            re.compile(r"\burlpatterns\b|\bpath\s*\(|\bre_path\s*\("),
            re.compile(r"@\s*(?:RestController|Controller)\b"),
        ),
    ),
    (
        "Auth and authorization controls",
        (
            re.compile(r"@\s*PreAuthorize\b|@\s*Secured\b|hasRole|hasAuthority"),
            re.compile(r"\b(?:auth|authorization|principal|session|tenant|role|permission)s?\b", re.I),
            re.compile(r"\bcsrf\b|\bcors\b|\bpermitAll\b|\brequires?\w*Role\b", re.I),
        ),
    ),
    (
        "Query, LDAP, and expression sinks",
        (
            re.compile(r"\b(?:SELECT|UPDATE|DELETE|INSERT)\b", re.I),
            re.compile(r"\b(?:createQuery|prepareStatement|JdbcTemplate|queryFor|entityManager)\b"),
            re.compile(r"\b(?:where|filter|ldap|LdapTemplate|objectClass)\b", re.I),
            re.compile(r"\b(?:rawQuery|aggregate|findOne|findMany|Prisma\.raw|\$where)\b"),
        ),
    ),
    (
        "Outbound fetch and SSRF surfaces",
        (
            re.compile(r"\b(?:fetch|axios|requests\.(?:get|post)|urllib|httpx)\b"),
            re.compile(r"\b(?:RestTemplate|WebClient|HttpClient|HttpURLConnection|new URL)\b"),
            re.compile(r"\b(?:callback|webhook|redirect|url|uri|endpoint)\b", re.I),
        ),
    ),
    (
        "Identifier, token, reference, and display helpers",
        (
            re.compile(r"\b(?:generate|generator|sequence|next|random|uuid)\w*\b", re.I),
            re.compile(r"\b(?:token|code|reference|ref|pnr)\w*\b", re.I),
            re.compile(r"\b(?:display|summary|raw|html|label|receipt)\w*\b", re.I),
        ),
    ),
    (
        "Rendering and raw HTML sinks",
        (
            re.compile(r"\b(?:innerHTML|outerHTML|dangerouslySetInnerHTML|v-html)\b"),
            re.compile(r"\b(?:render_template_string|mark_safe|safeHtml|rawHtml|th:utext)\b", re.I),
            re.compile(r"\b(?:template|html|view)\b", re.I),
        ),
    ),
    (
        "Verbose errors and config exposure",
        (
            re.compile(r"\b(?:getMessage|printStackTrace|stacktrace|debug|trace)\b", re.I),
            re.compile(r"\b(?:api[_-]?key|secret|token|password|connectionString)\b", re.I),
            re.compile(r"\b(?:actuator|env|heapdump|config|profile)\b", re.I),
        ),
    ),
    (
        "State-changing and privileged sinks",
        (
            re.compile(r"\b(?:save|delete|update|cancel|refund|approve|adjust|transfer)\s*\("),
            re.compile(r"\b(?:admin|internal|management|warehouse|booking|payment|invoice)\b", re.I),
            re.compile(r"@\s*(?:Post|Put|Delete|Patch)Mapping\b"),
        ),
    ),
    (
        "Safe controls and possible decoys",
        (
            re.compile(r"\b(?:validate|sanitize|escape|encode|allowlist|denylist|guard|check)\w*\b", re.I),
            re.compile(r"\b(?:BCrypt|Argon2|Encoder|CSRF|sameOrigin|sameSite)\b"),
            re.compile(r"\b(?:ReferenceGuards|safe|trusted|authorized|permission)\w*\b"),
        ),
    ),
)


def build_static_focus_queue(workspace: Path) -> StaticFocusQueue:
    """Build a deterministic source-only navigation queue for chained audits."""

    matches_by_category: dict[str, list[InventoryMatch]] = {
        category: [] for category, _patterns in CATEGORY_PATTERNS
    }
    total_matches = 0
    item_counter = 1
    for path in _iter_source_files(workspace):
        if total_matches >= MAX_TOTAL_MATCHES:
            break
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        relative = path.relative_to(workspace).as_posix()
        for line_number, line in enumerate(lines, start=1):
            if total_matches >= MAX_TOTAL_MATCHES:
                break
            normalized = line.strip()
            if not normalized:
                continue
            for category, patterns in CATEGORY_PATTERNS:
                bucket = matches_by_category[category]
                if len(bucket) >= MAX_MATCHES_PER_CATEGORY:
                    continue
                if any(pattern.search(normalized) for pattern in patterns):
                    bucket.append(
                        InventoryMatch(
                            category=category,
                            item_id=f"FQ{item_counter:03d}",
                            path=relative,
                            line=line_number,
                            snippet=_compact_snippet(normalized),
                        )
                    )
                    item_counter += 1
                    total_matches += 1
                    if total_matches >= MAX_TOTAL_MATCHES:
                        break

    return StaticFocusQueue(
        categories=tuple(
            FocusQueueCategory(category, tuple(matches_by_category[category]))
            for category, _patterns in CATEGORY_PATTERNS
        )
    )


def build_static_prepass(workspace: Path) -> str:
    """Build a compact, source-only inventory for benchmark prompts."""

    queue = build_static_focus_queue(workspace)
    return render_static_focus_queue(queue)


def render_static_focus_queue(queue: StaticFocusQueue) -> str:
    """Render the focus queue as prompt-ready Markdown."""

    lines_out = [
        "## Source-Derived Static Focus Queue",
        "",
        "This queue was generated from the sanitized current workspace only. It is a navigation aid, not ground truth.",
        "Use it to plan source-only coverage before drawing chained-audit conclusions.",
        "",
        "### Focus Queue Summary",
        "",
        "| Category | Items |",
        "|---|---:|",
    ]
    for category in queue.categories:
        lines_out.append(f"| {category.name} | {len(category.items)} |")
    lines_out.extend(
        [
            "",
            "### Coverage Instructions",
            "",
            "- Review focus items by category and connect only source-supported source-hop-sink paths.",
            "- Treat safe controls as path-specific: decide whether they block the exact candidate path or are merely nearby.",
            "- Use full repository-relative paths and line numbers from this queue when re-reading evidence.",
        ]
    )
    any_matches = False
    for category in queue.categories:
        lines_out.extend(["", f"### {category.name}"])
        if not category.items:
            lines_out.append("- No compact matches found.")
            continue
        any_matches = True
        for item in category.items:
            lines_out.append(f"- {item.item_id} `{item.path}:{item.line}` {item.snippet}")
    if not any_matches:
        lines_out.append("")
        lines_out.append("No high-signal source patterns were found in the sampled files.")
    return "\n".join(lines_out)


def _iter_source_files(workspace: Path) -> list[Path]:
    paths: list[Path] = []
    for path in workspace.rglob("*"):
        if not path.is_file():
            continue
        if path.name.lower() in REMOVED_BASENAMES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(workspace).parts[:-1]):
            continue
        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        paths.append(path)
    return sorted(paths, key=lambda item: item.relative_to(workspace).as_posix())


def _compact_snippet(value: str) -> str:
    value = re.sub(r"\s+", " ", value)
    if len(value) <= MAX_SNIPPET_CHARS:
        return value
    return value[: MAX_SNIPPET_CHARS - 3].rstrip() + "..."
