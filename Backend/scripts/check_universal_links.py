#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import plistlib
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SECRET_PATTERN = re.compile(r"(appsecret|secret|password|token|access_key|ak/sk)", re.IGNORECASE)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def read_plist(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as file:
            data = plistlib.load(file)
    except (FileNotFoundError, plistlib.InvalidFileException, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def clean_value(value: str) -> str:
    return value.strip().strip('"').strip("'")


def first_yml_value(text: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    return clean_value(match.group(1)) if match else ""


def release_yml_value(text: str, key: str) -> str:
    lines = text.splitlines()
    in_release = False
    release_indent = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if re.fullmatch(r"Release:\s*", stripped):
            in_release = True
            release_indent = indent
            continue
        if in_release and indent <= release_indent:
            break
        if in_release:
            match = re.match(rf"{re.escape(key)}:\s*(.+?)\s*$", stripped)
            if match:
                return clean_value(match.group(1))
    return ""


def aasa_app_ids(data: dict[str, Any]) -> set[str]:
    details = data.get("applinks", {}).get("details", [])
    if not isinstance(details, list):
        return set()
    app_ids: set[str] = set()
    for detail in details:
        if not isinstance(detail, dict):
            continue
        app_id = detail.get("appID")
        if isinstance(app_id, str):
            app_ids.add(app_id)
        values = detail.get("appIDs")
        if isinstance(values, list):
            app_ids.update(value for value in values if isinstance(value, str))
    return app_ids


def aasa_paths(data: dict[str, Any]) -> set[str]:
    details = data.get("applinks", {}).get("details", [])
    if not isinstance(details, list):
        return set()
    paths: set[str] = set()
    for detail in details:
        if not isinstance(detail, dict):
            continue
        values = detail.get("paths")
        if isinstance(values, list):
            paths.update(value for value in values if isinstance(value, str))
        components = detail.get("components")
        if isinstance(components, list):
            for component in components:
                if isinstance(component, dict) and isinstance(component.get("/"), str):
                    paths.add(component["/"])
    return paths


def path_matches(pattern: str, path: str) -> bool:
    if pattern == path:
        return True
    if pattern.endswith("*"):
        return path.startswith(pattern[:-1])
    return False


class Report:
    def __init__(self) -> None:
        self.checks: dict[str, dict[str, Any]] = {}

    def add(self, name: str, passed: bool, evidence: str, required: bool = True) -> None:
        self.checks[name] = {
            "passed": passed,
            "required": required,
            "evidence": evidence,
        }

    def to_dict(self, started_at: str, completed_at: str) -> dict[str, Any]:
        failed_required = [
            name
            for name, check in self.checks.items()
            if check["required"] and check["passed"] is not True
        ]
        return {
            "startedAt": started_at,
            "completedAt": completed_at,
            "containsSecrets": False,
            "passed": not failed_required,
            "failedRequiredChecks": failed_required,
            "checks": self.checks,
        }


def build_report(root: Path) -> dict[str, Any]:
    started_at = utc_now()
    report = Report()
    project_yml = read_text(root / "App/iOS/project.yml")
    server_py = read_text(root / "Backend/api/server.py")
    entitlements_path = root / "App/iOS/XiaoNaiPing/XiaoNaiPing.entitlements"
    entitlements = read_plist(entitlements_path)
    aasa_path = root / "Backend/static/apple-app-site-association"
    aasa_text = read_text(aasa_path)
    aasa = read_json(aasa_path)

    team_id = first_yml_value(project_yml, "DEVELOPMENT_TEAM")
    bundle_id = first_yml_value(project_yml, "PRODUCT_BUNDLE_IDENTIFIER")
    expected_app_id = f"{team_id}.{bundle_id}" if team_id and bundle_id else ""
    universal_link = release_yml_value(project_yml, "XNP_WECHAT_UNIVERSAL_LINK")
    associated_domain_setting = release_yml_value(project_yml, "XNP_ASSOCIATED_DOMAIN")
    parsed_link = urlparse(universal_link)
    link_host = parsed_link.netloc
    link_path = parsed_link.path or "/"

    report.add("aasaFilePresent", aasa_path.exists(), str(aasa_path))
    report.add("aasaValidJSON", bool(aasa), "AASA is valid JSON" if aasa else "AASA missing or invalid JSON")

    app_ids = aasa_app_ids(aasa)
    report.add(
        "aasaExpectedAppIDPresent",
        bool(expected_app_id) and expected_app_id in app_ids,
        f"expected {expected_app_id}; found {', '.join(sorted(app_ids)) or '<none>'}",
    )

    paths = aasa_paths(aasa)
    required_paths = {"/wechat/*", "/xiaonaiping/wechat/*"}
    missing_paths = sorted(required_paths - paths)
    report.add(
        "aasaWeChatCallbackPathsPresent",
        not missing_paths,
        "missing: " + ", ".join(missing_paths) if missing_paths else "AASA contains dedicated and transitional WeChat callback paths",
    )

    routes_ok = (
        '"/apple-app-site-association"' in server_py
        and '"/.well-known/apple-app-site-association"' in server_py
        and '"application/json; charset=utf-8"' in server_py
    )
    report.add(
        "backendAASARoutesConfigured",
        routes_ok,
        "backend serves root and .well-known AASA routes as application/json"
        if routes_ok
        else "backend AASA routes or content type are missing",
    )

    associated_domains = entitlements.get("com.apple.developer.associated-domains")
    if not isinstance(associated_domains, list):
        associated_domains = []
    effective_domains = [
        associated_domain_setting if value == "$(XNP_ASSOCIATED_DOMAIN)" else value
        for value in associated_domains
        if isinstance(value, str)
    ]
    report.add(
        "iosAssociatedDomainsEntitlementPresent",
        bool(effective_domains),
        ", ".join(effective_domains) if effective_domains else f"missing associated domains in {entitlements_path}",
    )
    report.add(
        "iosEntitlementsConfiguredInProject",
        "XiaoNaiPing/XiaoNaiPing.entitlements" in project_yml,
        "project.yml points at XiaoNaiPing.entitlements"
        if "XiaoNaiPing/XiaoNaiPing.entitlements" in project_yml
        else "project.yml missing entitlements path",
    )
    report.add(
        "releaseWeChatUniversalLinkConfigured",
        universal_link.startswith("https://") and bool(link_host),
        universal_link or "<empty>",
    )

    expected_domain = f"applinks:{link_host}" if link_host else ""
    report.add(
        "universalLinkMatchesAssociatedDomain",
        bool(expected_domain) and expected_domain in effective_domains,
        f"expected {expected_domain}; effective domains: {', '.join(effective_domains) or '<none>'}",
    )
    report.add(
        "universalLinkPathCoveredByAASA",
        bool(link_path) and any(path_matches(pattern, link_path) for pattern in paths),
        f"link path {link_path}; AASA paths: {', '.join(sorted(paths)) or '<none>'}",
    )
    report.add(
        "aasaContainsNoSecrets",
        SECRET_PATTERN.search(aasa_text) is None,
        "AASA contains no secret-like markers"
        if SECRET_PATTERN.search(aasa_text) is None
        else "AASA contains secret-like marker",
    )

    return report.to_dict(started_at, utc_now())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(repo_root()))
    parser.add_argument("--output", default=str(repo_root() / "Backend/proof/universal-links.json"))
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    result = build_report(Path(args.repo_root).resolve())
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if result["passed"]:
        print(f"universal links proof passed: {output_path}")
        return

    failed = ", ".join(result["failedRequiredChecks"])
    print(f"universal links proof incomplete: {output_path}", file=sys.stderr)
    print(f"failed required checks: {failed}", file=sys.stderr)
    if not args.allow_incomplete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
