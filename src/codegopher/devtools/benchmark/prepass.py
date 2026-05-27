"""Source-derived static inventory for chained-audit benchmark prompts."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
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
MAX_CANDIDATES_PER_CATEGORY = 64
MAX_TOTAL_MATCHES = 128
MAX_TOTAL_CANDIDATES = 512
MAX_SOURCE_GRAPH_EDGES = 20
MAX_SNIPPET_CHARS = 180
REMOVED_BASENAMES = {"readme.md", "impl_plan.md", ".vulns", "vulns.json", "scenarios.md"}
TOKEN_STOPWORDS = {
    "admin",
    "api",
    "app",
    "auth",
    "class",
    "config",
    "controller",
    "data",
    "entity",
    "error",
    "get",
    "html",
    "http",
    "java",
    "json",
    "main",
    "model",
    "post",
    "public",
    "return",
    "route",
    "service",
    "src",
    "string",
    "test",
    "this",
    "true",
    "type",
    "util",
    "void",
}
SOURCE_GRAPH_SOURCE_CATEGORIES = {
    "Routes and entry points",
    "Auth and authorization controls",
    "Identifier, token, reference, and display helpers",
}
SOURCE_GRAPH_TARGET_CATEGORIES = {
    "Auth and authorization controls",
    "Query, LDAP, and expression sinks",
    "Outbound fetch and SSRF surfaces",
    "Identifier, token, reference, and display helpers",
    "Rendering and raw HTML sinks",
    "Verbose errors and config exposure",
    "State-changing and privileged sinks",
    "Safe controls and possible decoys",
}
HIGH_RISK_SOURCE_FAMILIES = {
    "controllers_routes",
    "auth_session",
    "config_secrets",
    "validators",
    "uploads",
    "jobs",
    "webhooks_outbound",
    "repositories_query",
    "state_changing",
    "tsx_render_sink",
    "static_js_sink",
    "static_html_signal",
}
SOURCE_FAMILY_LABELS = {
    "controllers_routes": "controllers/routes",
    "auth_session": "auth/session",
    "config_secrets": "config/secrets",
    "validators": "validators",
    "uploads": "uploads",
    "jobs": "jobs/background work",
    "webhooks_outbound": "webhooks/outbound calls",
    "repositories_query": "repositories/query sinks",
    "state_changing": "state-changing sinks",
    "tsx_render_sink": "TS/TSX render sinks",
    "static_js_sink": "static JS sinks",
    "static_html_signal": "static HTML signals",
    "css_low_signal": "CSS/static styling",
    "general": "general source",
}
SOURCE_FAMILY_DISCOVERY_ORDER = (
    "controllers_routes",
    "auth_session",
    "config_secrets",
    "validators",
    "uploads",
    "repositories_query",
    "state_changing",
    "tsx_render_sink",
    "static_js_sink",
    "webhooks_outbound",
    "jobs",
    "static_html_signal",
)


@dataclass(frozen=True)
class InventoryMatch:
    category: str
    item_id: str
    path: str
    line: int
    snippet: str
    source_family: str = "general"
    priority: int = 50


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


@dataclass(frozen=True)
class SourceGraphEdge:
    edge_id: str
    source_category: str
    source_path: str
    source_line: int
    target_category: str
    target_path: str
    target_line: int
    relation: str
    shared_tokens: tuple[str, ...]


@dataclass(frozen=True)
class SourceGraph:
    edges: tuple[SourceGraphEdge, ...]


CATEGORY_PATTERNS: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    (
        "Routes and entry points",
        (
            re.compile(r"@\s*(?:Get|Post|Put|Delete|Patch|Request)Mapping\b"),
            re.compile(r"\b(?:app|router)\.(?:get|post|put|delete|patch)\s*\("),
            re.compile(r"@\s*(?:app|bp)\.route\s*\("),
            re.compile(r"\badd_url_rule\s*\("),
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
            re.compile(
                r"\b(?:api[_-]?key|secret[_-]?key|secret|token|password|connectionString)\b",
                re.I,
            ),
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

    candidates_by_category: dict[str, list[InventoryMatch]] = {
        category: [] for category, _patterns in CATEGORY_PATTERNS
    }
    total_candidates = 0
    for path in _iter_source_files(workspace):
        if total_candidates >= MAX_TOTAL_CANDIDATES:
            break
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        relative = path.relative_to(workspace).as_posix()
        for line_number, line in enumerate(lines, start=1):
            if total_candidates >= MAX_TOTAL_CANDIDATES:
                break
            normalized = line.strip()
            if not normalized:
                continue
            for category, patterns in CATEGORY_PATTERNS:
                bucket = candidates_by_category[category]
                if len(bucket) >= MAX_CANDIDATES_PER_CATEGORY:
                    continue
                if any(pattern.search(normalized) for pattern in patterns):
                    snippet = _compact_snippet(normalized)
                    family, priority = _classify_source_family(
                        relative,
                        category,
                        snippet,
                    )
                    bucket.append(
                        InventoryMatch(
                            category=category,
                            item_id="",
                            path=relative,
                            line=line_number,
                            snippet=snippet,
                            source_family=family,
                            priority=priority,
                        )
                    )
                    total_candidates += 1
                    if total_candidates >= MAX_TOTAL_CANDIDATES:
                        break

    item_counter = 1
    matches_by_category: dict[str, list[InventoryMatch]] = {}
    for category, _patterns in CATEGORY_PATTERNS:
        selected: list[InventoryMatch] = []
        for match in _select_representative_matches(candidates_by_category[category]):
            selected.append(replace(match, item_id=f"FQ{item_counter:03d}"))
            item_counter += 1
            if item_counter > MAX_TOTAL_MATCHES:
                break
        matches_by_category[category] = selected
        if item_counter > MAX_TOTAL_MATCHES:
            break

    return StaticFocusQueue(
        categories=tuple(
            FocusQueueCategory(category, tuple(matches_by_category.get(category, ())))
            for category, _patterns in CATEGORY_PATTERNS
        )
    )


def build_static_prepass(workspace: Path) -> str:
    """Build a compact, source-only inventory for benchmark prompts."""

    queue = build_static_focus_queue(workspace)
    return render_static_focus_queue(queue)


def render_static_focus_queue(queue: StaticFocusQueue) -> str:
    """Render the focus queue as prompt-ready Markdown."""

    graph = build_source_graph(queue)
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
    lines_out.extend(_render_high_risk_family_targets(queue))
    lines_out.extend(["", "### Lightweight Source Graph"])
    if graph.edges:
        lines_out.extend(
            [
                "",
                "These source-derived edges are approximate navigation hints inferred from file names, symbols, snippets, and same-file proximity.",
                "Validate every edge by reading source before using it as evidence.",
            ]
        )
        for edge in graph.edges:
            tokens = ", ".join(edge.shared_tokens) if edge.shared_tokens else "same file"
            lines_out.append(
                f"- {edge.edge_id} {edge.source_category} `{edge.source_path}:{edge.source_line}` "
                f"-> {edge.target_category} `{edge.target_path}:{edge.target_line}` "
                f"({edge.relation}; tokens: {tokens})"
            )
    else:
        lines_out.append("")
        lines_out.append("- No compact source graph edges inferred from the sampled source.")
    any_matches = False
    for category in queue.categories:
        lines_out.extend(["", f"### {category.name}"])
        if not category.items:
            lines_out.append("- No compact matches found.")
            continue
        any_matches = True
        for item in category.items:
            family = SOURCE_FAMILY_LABELS.get(item.source_family, item.source_family)
            lines_out.append(
                f"- {item.item_id} `{item.path}:{item.line}` [{family}] {item.snippet}"
            )
    if not any_matches:
        lines_out.append("")
        lines_out.append("No high-signal source patterns were found in the sampled files.")
    return "\n".join(lines_out)


def _render_high_risk_family_targets(queue: StaticFocusQueue) -> list[str]:
    lines: list[str] = [
        "",
        "### High-Risk Source Family Coverage Targets",
        "",
        "Read representative files from each listed family before final no-chain or complete-chain conclusions.",
    ]
    rendered_any = False
    for family in SOURCE_FAMILY_DISCOVERY_ORDER:
        items = [
            item
            for category in queue.categories
            for item in category.items
            if item.source_family == family
        ]
        if not items:
            continue
        rendered_any = True
        label = SOURCE_FAMILY_LABELS.get(family, family)
        lines.append(f"- {label}:")
        for item in _rank_family_targets(items)[:6]:
            lines.append(f"  - {item.item_id} `{item.path}:{item.line}` {item.snippet}")
    if not rendered_any:
        lines.append("- No high-risk source-family targets were inferred.")
    return lines


def build_source_graph(queue: StaticFocusQueue) -> SourceGraph:
    """Infer a bounded source-only graph from focus queue items."""

    sources = _items_for_categories(queue, SOURCE_GRAPH_SOURCE_CATEGORIES)
    targets = _items_for_categories(queue, SOURCE_GRAPH_TARGET_CATEGORIES)
    ranked: list[tuple[int, int, InventoryMatch, InventoryMatch, tuple[str, ...], str]] = []
    order = 0
    for source in sources:
        source_tokens = _item_tokens(source)
        for target in targets:
            if source == target:
                continue
            if source.path == target.path and source.category == target.category:
                continue
            if source.category == target.category and source.path != target.path:
                continue
            target_tokens = _item_tokens(target)
            shared = tuple(sorted(source_tokens & target_tokens))
            same_file = source.path == target.path
            family_bonus = _chain_edge_bonus(source, target)
            if not shared and not same_file and family_bonus < 60:
                continue
            relation = _edge_relation(source, target, shared, same_file)
            score = (
                len(shared) * 10
                + (5 if same_file else 0)
                + family_bonus
                + max(source.priority, target.priority) // 20
            )
            ranked.append((score, order, source, target, shared[:5], relation))
            order += 1

    ranked.sort(
        key=lambda item: (
            -item[0],
            item[2].path,
            item[2].line,
            item[3].path,
            item[3].line,
            item[1],
        )
    )
    edges: list[SourceGraphEdge] = []
    seen: set[tuple[str, int, str, int, str]] = set()
    for _score, _order, source, target, shared, relation in ranked:
        key = (source.path, source.line, target.path, target.line, target.category)
        if key in seen:
            continue
        seen.add(key)
        edges.append(
            SourceGraphEdge(
                edge_id=f"SG{len(edges) + 1:03d}",
                source_category=source.category,
                source_path=source.path,
                source_line=source.line,
                target_category=target.category,
                target_path=target.path,
                target_line=target.line,
                relation=relation,
                shared_tokens=shared,
            )
        )
        if len(edges) >= MAX_SOURCE_GRAPH_EDGES:
            break
    return SourceGraph(edges=tuple(edges))


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


def _items_for_categories(
    queue: StaticFocusQueue, categories: set[str]
) -> tuple[InventoryMatch, ...]:
    return tuple(
        item
        for category in queue.categories
        if category.name in categories
        for item in category.items
    )


def _select_representative_matches(
    matches: list[InventoryMatch],
) -> tuple[InventoryMatch, ...]:
    ordered = sorted(
        matches,
        key=lambda item: (
            -item.priority,
            item.source_family,
            item.path,
            item.line,
            item.snippet,
        ),
    )
    seen_paths: set[str] = set()
    seen_families: set[str] = set()
    representatives: list[InventoryMatch] = []
    remaining: list[InventoryMatch] = []
    for match in ordered:
        if match.path in seen_paths:
            remaining.append(match)
            continue
        seen_paths.add(match.path)
        if match.source_family in seen_families and match.priority < 90:
            remaining.append(match)
            continue
        seen_families.add(match.source_family)
        representatives.append(match)
    remaining = sorted(
        remaining,
        key=lambda item: (
            -item.priority,
            item.source_family,
            item.path,
            item.line,
            item.snippet,
        ),
    )
    return tuple((representatives + remaining)[:MAX_MATCHES_PER_CATEGORY])


def _rank_family_targets(items: list[InventoryMatch]) -> tuple[InventoryMatch, ...]:
    ordered = sorted(
        items,
        key=lambda item: (
            -_family_target_score(item),
            item.path,
            item.line,
            item.snippet,
        ),
    )
    seen_paths: set[str] = set()
    ranked: list[InventoryMatch] = []
    for item in ordered:
        if item.path in seen_paths:
            continue
        seen_paths.add(item.path)
        ranked.append(item)
    return tuple(ranked)


def _family_target_score(item: InventoryMatch) -> int:
    category_bonus = {
        "Routes and entry points": 35,
        "State-changing and privileged sinks": 30,
        "Auth and authorization controls": 25,
        "Query, LDAP, and expression sinks": 20,
        "Outbound fetch and SSRF surfaces": 20,
        "Rendering and raw HTML sinks": 20,
        "Safe controls and possible decoys": 15,
        "Verbose errors and config exposure": 10,
    }.get(item.category, 0)
    combined = f"{item.path.lower()} {item.snippet.lower()}"
    score = item.priority + category_bonus
    if "/static/" in combined and item.source_family not in {
        "static_js_sink",
        "static_html_signal",
    }:
        score -= 25
    if "health" in combined:
        score -= 45
    if _contains_any(
        combined,
        (
            "admin",
            "auth",
            "bulk",
            "callback",
            "create",
            "delete",
            "flag",
            "login",
            "product",
            "report",
            "secret",
            "session",
            "settings",
            "supplier",
            "update",
            "upload",
            "user",
            "validator",
            "webhook",
        ),
    ):
        score += 25
    if "settings.py" in combined or "secret_key" in combined:
        score += 30
    if "add_url_rule" in combined:
        score += 15
    if "def " in combined or combined.strip().startswith("@"):
        score += 10
    return score


def _item_tokens(item: InventoryMatch) -> set[str]:
    text = f"{item.path} {item.snippet}"
    raw_tokens = re.findall(r"[A-Za-z][A-Za-z0-9]{2,}", text)
    tokens: set[str] = set()
    for token in raw_tokens:
        for part in _split_identifier(token):
            normalized = part.lower()
            if len(normalized) < 3 or normalized in TOKEN_STOPWORDS:
                continue
            tokens.add(normalized)
    return tokens


def _split_identifier(value: str) -> tuple[str, ...]:
    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    return tuple(re.split(r"[^A-Za-z0-9]+", expanded))


def _edge_relation(
    source: InventoryMatch,
    target: InventoryMatch,
    shared_tokens: tuple[str, ...],
    same_file: bool,
) -> str:
    if _chain_edge_bonus(source, target) >= 40:
        return "chain-shaped source family edge"
    if same_file:
        return "same-file proximity"
    if source.path.rsplit("/", 1)[0] == target.path.rsplit("/", 1)[0]:
        return "same-directory shared symbols"
    if shared_tokens:
        return "shared source symbols"
    return "source-derived proximity"


def _classify_source_family(path: str, category: str, snippet: str) -> tuple[str, int]:
    path_l = path.lower()
    snippet_l = snippet.lower()
    suffix = Path(path_l).suffix
    combined = f"{path_l} {snippet_l}"
    path_parts = set(Path(path_l).parts)

    if suffix in {".tsx", ".jsx"} and _has_render_sink(snippet_l):
        return "tsx_render_sink", 125
    if _contains_any(combined, ("controller", "controllers", "routes", "_routes", "route")):
        priority = 120
        if "health" in snippet_l and "route" in snippet_l:
            priority = 85
        return "controllers_routes", priority
    if _contains_any(combined, ("auth", "session", "principal", "role", "permission", "login")):
        return "auth_session", 118
    if _contains_any(combined, ("settings", "config", "secret", "api_key", "apikey", "password")):
        priority = 124 if "settings.py" in path_l or "secret_key" in combined else 114
        return "config_secrets", priority
    if _contains_any(combined, ("validator", "validators", "validate_", "validate", "guard")):
        return "validators", 110
    if _contains_any(combined, ("upload", "bulk", "csv", "multipart", "file")):
        return "uploads", 108
    if _contains_any(combined, ("job", "queue", "scheduler", "consumer", "worker")):
        return "jobs", 106
    if _contains_any(
        combined,
        ("webhook", "callback", "requests.", "httpx", "urllib", "fetch(", "axios"),
    ):
        return "webhooks_outbound", 104
    if _contains_any(
        combined,
        ("repository", "repositories", "dao", "query", "select ", "update ", "delete ", "insert "),
    ):
        return "repositories_query", 102
    if category == "State-changing and privileged sinks" or _contains_any(
        combined,
        ("create_", "update_", "delete_", "save_", "approve", "refund", "transfer", "admin"),
    ):
        return "state_changing", 98
    if suffix in {".ts", ".tsx", ".js", ".jsx"} and _has_render_sink(snippet_l):
        return "static_js_sink", 92
    if suffix in {".js", ".jsx", ".ts", ".tsx"} and _contains_any(
        combined,
        ("fetch(", "token", "credential", "innerhtml", "api/auth", "api/"),
    ):
        return "static_js_sink", 84
    if suffix == ".html" and _contains_any(
        combined,
        ("credential", "password", "token", "script", "form", "input", "admin"),
    ):
        return "static_html_signal", 72
    if suffix == ".css" or "static/css" in path_l or "css" in path_parts:
        if _contains_any(snippet_l, ("@import", "url(")):
            return "css_low_signal", 35
        return "css_low_signal", 10
    if "static" in path_parts:
        return "general", 35
    return "general", 50


def _chain_edge_bonus(source: InventoryMatch, target: InventoryMatch) -> int:
    pair = (source.source_family, target.source_family)
    chain_pairs = {
        ("controllers_routes", "auth_session"),
        ("controllers_routes", "state_changing"),
        ("controllers_routes", "repositories_query"),
        ("controllers_routes", "validators"),
        ("auth_session", "state_changing"),
        ("auth_session", "config_secrets"),
        ("config_secrets", "auth_session"),
        ("validators", "controllers_routes"),
        ("validators", "uploads"),
        ("uploads", "state_changing"),
        ("webhooks_outbound", "webhooks_outbound"),
        ("webhooks_outbound", "jobs"),
        ("jobs", "webhooks_outbound"),
        ("repositories_query", "state_changing"),
        ("static_js_sink", "repositories_query"),
        ("static_js_sink", "controllers_routes"),
        ("tsx_render_sink", "controllers_routes"),
        ("controllers_routes", "tsx_render_sink"),
        ("state_changing", "repositories_query"),
    }
    if pair in chain_pairs:
        return 60
    if (
        source.source_family in HIGH_RISK_SOURCE_FAMILIES
        and target.source_family in HIGH_RISK_SOURCE_FAMILIES
    ):
        return 25
    return 0


def _contains_any(value: str, needles: tuple[str, ...]) -> bool:
    return any(needle in value for needle in needles)


def _has_render_sink(value: str) -> bool:
    return any(
        marker in value
        for marker in (
            "innerhtml",
            "outerhtml",
            "dangerouslysetinnerhtml",
            "v-html",
            "render_template_string",
            "mark_safe",
            "rawhtml",
            "safehtml",
            "th:utext",
        )
    )
