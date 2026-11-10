import re
from typing import Tuple, Dict, Any, List

class SecurityRuleChecker:
    """
    Hardened inspector that scans tool call arguments for destructive patterns,
    injection attacks, obfuscated payloads, and ReDoS-safe regexes.
    """

    MAX_RECURSION_DEPTH = 20

    # Hardened, ReDoS-safe patterns (no catastrophic backtracking)
    DEFAULT_BLOCKED_PATTERNS = [
        # SQL destructives & bypasses
        (r"(?i)\bDROP\s+(?:TABLE|DATABASE|SCHEMA|INDEX|VIEW)\b", "Destructive SQL DROP statement detected"),
        (r"(?i)\bTRUNCATE\s+(?:TABLE)?\b", "Destructive SQL TRUNCATE statement detected"),
        (r"(?i)\bDELETE\s+FROM\s+[a-zA-Z0-9_]+\s*(?:;|\bWHERE\s+1\s*=\s*1\b|$)", "Unrestricted SQL DELETE statement detected"),
        (r"(?i)\bALTER\s+TABLE\s+[a-zA-Z0-9_]+\s+DROP\b", "Destructive SQL ALTER TABLE DROP detected"),
        (r"(?i)(?:--|#|/\*.*?\*/)\s*(?:DROP|DELETE|TRUNCATE)", "SQL comment obfuscation injection detected"),
        (r"(?i)\bEXEC(?:UTE)?\s*\(\s*(?:xp_cmdshell|sp_executesql)\b", "Privileged database shell execution detected"),

        # Shell / OS destructives & dangerous execution
        (r"(?i)\brm\s+-[a-z0-9]*[rf][a-z0-9]*\s+", "Destructive recursive force delete (rm -rf) detected"),
        (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Linux fork bomb pattern detected"),
        (r"(?i)\bformat\s+[a-z]:", "Disk format command detected"),
        (r">\s*/dev/sd[a-z]", "Raw disk overwrite pattern detected"),
        (r"(?i)\bmkfs(?:\.[a-z0-9]+)?\s+", "Filesystem creation/format pattern detected"),
        (r"(?i)\bchmod\s+(?:-R\s+)?777\b", "Insecure global permission assignment (chmod 777) detected"),
        (r"(?i)(?:curl|wget)\s+[^|;]+\|\s*(?:ba)?sh\b", "Remote code execution pipe to shell (curl|sh) detected"),
        (r"(?i)\b(?:eval|exec)\s*\(\s*(?:base64_decode|atob)\b", "Obfuscated payload execution (eval/base64) detected"),
        (r"(?i)\bpowershell\s+-(?:e|enc|encodedcommand)\b", "Encoded PowerShell execution detected")
    ]

    @classmethod
    def check_arguments(cls, arguments: Dict[str, Any], custom_patterns: List[str] = None) -> Tuple[bool, str]:
        """
        Scans all string values in arguments for security violations with depth protection.
        Returns:
            (is_safe, violation_reason)
        """
        patterns_to_check = list(cls.DEFAULT_BLOCKED_PATTERNS)
        if custom_patterns:
            for pat in custom_patterns:
                try:
                    re.compile(pat)
                    patterns_to_check.append((pat, f"Custom security rule violation: {pat}"))
                except re.error:
                    pass

        def extract_strings(obj, depth=0):
            if depth > cls.MAX_RECURSION_DEPTH:
                return
            if isinstance(obj, str):
                yield obj
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(k, str):
                        yield k
                    yield from extract_strings(v, depth + 1)
            elif isinstance(obj, (list, tuple, set)):
                for item in obj:
                    yield from extract_strings(item, depth + 1)

        try:
            for text in extract_strings(arguments):
                if not isinstance(text, str):
                    continue
                for pattern, reason in patterns_to_check:
                    if re.search(pattern, text):
                        return False, reason
            return True, "Passed security inspection"
        except Exception as e:
            # Fail closed on unexpected parsing errors
            return False, f"Security scanning error: {str(e)}"
