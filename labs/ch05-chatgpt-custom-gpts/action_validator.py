#!/usr/bin/env python3
"""
OpenAPI Schema Validator for ChatGPT Actions

This lab validates OpenAPI schemas for GPT compatibility including:
- Schema structure (required fields, proper formatting)
- GPT-specific requirements (operationId, descriptions)
- Parameter validation (types, constraints)
- Security configuration
- Common pitfalls

Usage:
    # Validate schema file
    python action_validator.py --schema weather_api.yaml

    # Validate with verbose output
    python action_validator.py --schema weather_api.yaml --verbose

    # Generate validation report
    python action_validator.py --schema weather_api.yaml --output validation_report.json

References:
    OpenAPI 3.1 Specification: https://spec.openapis.org/oas/v3.1.0
    OpenAI Actions Documentation: https://platform.openai.com/docs/actions
"""

import argparse
import json
import yaml
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Single validation issue."""
    severity: str
    category: str
    message: str
    location: str
    recommendation: str


@dataclass
class ValidationReport:
    """Complete validation report."""
    schema_valid: bool
    error_count: int
    warning_count: int
    info_count: int
    issues: List[ValidationIssue]
    summary: str


# =============================================================================
# OpenAPI Schema Validator
# =============================================================================

class ActionSchemaValidator:
    """Validates OpenAPI schemas for ChatGPT Actions."""

    def __init__(self, schema: Dict, verbose: bool = False):
        self.schema = schema
        self.verbose = verbose
        self.issues: List[ValidationIssue] = []

    def validate(self) -> ValidationReport:
        """Run all validation checks."""
        if self.verbose:
            print("Starting validation...\n")

        # Core structure validation
        self._validate_structure()

        # Field presence validation
        self._validate_required_fields()

        # GPT-specific validation
        self._validate_gpt_requirements()

        # Parameter validation
        self._validate_parameters()

        # Security validation
        self._validate_security()

        # Best practices
        self._check_best_practices()

        # Generate report
        return self._generate_report()

    def _validate_structure(self):
        """Validate basic OpenAPI structure."""
        if self.verbose:
            print("Checking basic structure...")

        # Check OpenAPI version
        if "openapi" not in self.schema:
            self._add_issue(
                Severity.ERROR,
                "structure",
                "Missing 'openapi' field",
                "root",
                "Add: openapi: 3.1.0"
            )
        else:
            version = self.schema["openapi"]
            if not version.startswith("3."):
                self._add_issue(
                    Severity.ERROR,
                    "structure",
                    f"Unsupported OpenAPI version: {version}",
                    "root.openapi",
                    "Use OpenAPI 3.0.x or 3.1.x"
                )

        # Check info section
        if "info" not in self.schema:
            self._add_issue(
                Severity.ERROR,
                "structure",
                "Missing 'info' section",
                "root",
                "Add info section with title, description, version"
            )
        else:
            info = self.schema["info"]
            for field in ["title", "version"]:
                if field not in info:
                    self._add_issue(
                        Severity.ERROR,
                        "structure",
                        f"Missing 'info.{field}'",
                        "root.info",
                        f"Add: {field}: <value>"
                    )

            if "description" not in info:
                self._add_issue(
                    Severity.WARNING,
                    "structure",
                    "Missing 'info.description'",
                    "root.info",
                    "Add description to help GPT understand the API purpose"
                )

        # Check servers
        if "servers" not in self.schema:
            self._add_issue(
                Severity.ERROR,
                "structure",
                "Missing 'servers' section",
                "root",
                "Add: servers:\n  - url: https://api.example.com"
            )
        elif not self.schema["servers"]:
            self._add_issue(
                Severity.ERROR,
                "structure",
                "'servers' list is empty",
                "root.servers",
                "Add at least one server URL"
            )

        # Check paths
        if "paths" not in self.schema:
            self._add_issue(
                Severity.ERROR,
                "structure",
                "Missing 'paths' section",
                "root",
                "Add paths section with at least one endpoint"
            )
        elif not self.schema["paths"]:
            self._add_issue(
                Severity.ERROR,
                "structure",
                "'paths' section is empty",
                "root.paths",
                "Define at least one endpoint"
            )

    def _validate_required_fields(self):
        """Validate presence of required fields."""
        if self.verbose:
            print("Checking required fields...")

        if "paths" not in self.schema:
            return

        for path, methods in self.schema["paths"].items():
            for method, operation in methods.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    continue  # Skip non-HTTP methods (e.g., $ref)

                location = f"paths.{path}.{method}"

                # operationId is critical for GPTs
                if "operationId" not in operation:
                    self._add_issue(
                        Severity.ERROR,
                        "required_fields",
                        f"Missing 'operationId' for {method.upper()} {path}",
                        location,
                        "Add unique operationId (e.g., getCurrentWeather)"
                    )

                # summary helps GPT understand when to use the operation
                if "summary" not in operation:
                    self._add_issue(
                        Severity.WARNING,
                        "required_fields",
                        f"Missing 'summary' for {method.upper()} {path}",
                        location,
                        "Add brief summary (GPT uses this to decide when to call)"
                    )

                # description provides detailed context
                if "description" not in operation:
                    self._add_issue(
                        Severity.INFO,
                        "required_fields",
                        f"Missing 'description' for {method.upper()} {path}",
                        location,
                        "Add detailed description to guide GPT usage"
                    )

    def _validate_gpt_requirements(self):
        """Validate GPT-specific requirements."""
        if self.verbose:
            print("Checking GPT compatibility...")

        if "paths" not in self.schema:
            return

        operation_ids = set()

        for path, methods in self.schema["paths"].items():
            for method, operation in methods.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    continue

                location = f"paths.{path}.{method}"

                # Check operationId uniqueness
                if "operationId" in operation:
                    op_id = operation["operationId"]
                    if op_id in operation_ids:
                        self._add_issue(
                            Severity.ERROR,
                            "gpt_requirements",
                            f"Duplicate operationId: {op_id}",
                            location,
                            "Use unique operationId for each operation"
                        )
                    operation_ids.add(op_id)

                    # Check operationId naming convention
                    if not self._is_camel_case(op_id):
                        self._add_issue(
                            Severity.WARNING,
                            "gpt_requirements",
                            f"operationId should be camelCase: {op_id}",
                            location,
                            "Use camelCase (e.g., getCurrentWeather, not get_current_weather)"
                        )

                # Check for overly complex nesting
                if "requestBody" in operation:
                    depth = self._check_nesting_depth(operation["requestBody"])
                    if depth > 3:
                        self._add_issue(
                            Severity.WARNING,
                            "gpt_requirements",
                            f"Request body has {depth} levels of nesting (max 3 recommended)",
                            f"{location}.requestBody",
                            "Flatten structure or split into multiple operations"
                        )

    def _validate_parameters(self):
        """Validate parameter definitions."""
        if self.verbose:
            print("Checking parameters...")

        if "paths" not in self.schema:
            return

        for path, methods in self.schema["paths"].items():
            for method, operation in methods.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    continue

                location = f"paths.{path}.{method}"

                if "parameters" in operation:
                    for i, param in enumerate(operation["parameters"]):
                        param_location = f"{location}.parameters[{i}]"

                        # Check required parameter fields
                        for field in ["name", "in"]:
                            if field not in param:
                                self._add_issue(
                                    Severity.ERROR,
                                    "parameters",
                                    f"Parameter missing '{field}'",
                                    param_location,
                                    f"Add: {field}: <value>"
                                )

                        # Check description
                        if "description" not in param:
                            param_name = param.get("name", f"parameter[{i}]")
                            self._add_issue(
                                Severity.WARNING,
                                "parameters",
                                f"Parameter '{param_name}' missing description",
                                param_location,
                                "Add description (GPT uses this to understand parameter purpose)"
                            )

                        # Check schema
                        if "schema" not in param:
                            param_name = param.get("name", f"parameter[{i}]")
                            self._add_issue(
                                Severity.ERROR,
                                "parameters",
                                f"Parameter '{param_name}' missing schema",
                                param_location,
                                "Add schema with type definition"
                            )
                        else:
                            schema = param["schema"]
                            if "type" not in schema:
                                self._add_issue(
                                    Severity.ERROR,
                                    "parameters",
                                    f"Parameter schema missing 'type'",
                                    f"{param_location}.schema",
                                    "Add type (string, integer, boolean, etc.)"
                                )

                            # Recommend enum for constrained values
                            if schema.get("type") == "string" and "enum" not in schema:
                                if param.get("name") in ["status", "type", "category", "format"]:
                                    self._add_issue(
                                        Severity.INFO,
                                        "parameters",
                                        f"Consider using 'enum' for '{param.get('name')}'",
                                        f"{param_location}.schema",
                                        "If values are constrained, use enum: [val1, val2]"
                                    )

    def _validate_security(self):
        """Validate security configuration."""
        if self.verbose:
            print("Checking security configuration...")

        # Check if security is defined
        has_global_security = "security" in self.schema
        has_security_schemes = "components" in self.schema and "securitySchemes" in self.schema.get("components", {})

        if has_global_security and not has_security_schemes:
            self._add_issue(
                Severity.ERROR,
                "security",
                "Global security defined but no securitySchemes",
                "root.security",
                "Define securitySchemes in components"
            )

        if has_security_schemes:
            schemes = self.schema["components"]["securitySchemes"]
            for name, scheme in schemes.items():
                location = f"components.securitySchemes.{name}"

                if "type" not in scheme:
                    self._add_issue(
                        Severity.ERROR,
                        "security",
                        f"Security scheme '{name}' missing 'type'",
                        location,
                        "Add type (apiKey, oauth2, http)"
                    )
                    continue

                scheme_type = scheme["type"]

                # Validate API Key schemes
                if scheme_type == "apiKey":
                    if "in" not in scheme:
                        self._add_issue(
                            Severity.ERROR,
                            "security",
                            f"API Key scheme '{name}' missing 'in'",
                            location,
                            "Add: in: header (or query, cookie)"
                        )
                    if "name" not in scheme:
                        self._add_issue(
                            Severity.ERROR,
                            "security",
                            f"API Key scheme '{name}' missing 'name'",
                            location,
                            "Add: name: X-API-Key (or custom header name)"
                        )

                # Validate OAuth2 schemes
                elif scheme_type == "oauth2":
                    if "flows" not in scheme:
                        self._add_issue(
                            Severity.ERROR,
                            "security",
                            f"OAuth2 scheme '{name}' missing 'flows'",
                            location,
                            "Add flows (authorizationCode, clientCredentials, etc.)"
                        )

    def _check_best_practices(self):
        """Check best practices."""
        if self.verbose:
            print("Checking best practices...")

        # Check HTTPS
        if "servers" in self.schema:
            for i, server in enumerate(self.schema["servers"]):
                if "url" in server:
                    url = server["url"]
                    if url.startswith("http://") and "localhost" not in url:
                        self._add_issue(
                            Severity.WARNING,
                            "best_practices",
                            f"Server URL uses HTTP (not HTTPS): {url}",
                            f"servers[{i}].url",
                            "Use HTTPS for production APIs"
                        )

        # Check for version in URL
        if "servers" in self.schema:
            for i, server in enumerate(self.schema["servers"]):
                if "url" in server:
                    url = server["url"]
                    if "/v" not in url and "/api" in url:
                        self._add_issue(
                            Severity.INFO,
                            "best_practices",
                            "Consider including API version in URL",
                            f"servers[{i}].url",
                            "Example: https://api.example.com/v1"
                        )

    def _add_issue(self, severity: Severity, category: str, message: str, location: str, recommendation: str):
        """Add validation issue."""
        self.issues.append(ValidationIssue(
            severity=severity.value,
            category=category,
            message=message,
            location=location,
            recommendation=recommendation
        ))

    def _generate_report(self) -> ValidationReport:
        """Generate validation report."""
        error_count = sum(1 for i in self.issues if i.severity == "error")
        warning_count = sum(1 for i in self.issues if i.severity == "warning")
        info_count = sum(1 for i in self.issues if i.severity == "info")

        schema_valid = error_count == 0

        if schema_valid and warning_count == 0:
            summary = "✓ Schema is valid and follows best practices"
        elif schema_valid:
            summary = f"✓ Schema is valid but has {warning_count} warning(s)"
        else:
            summary = f"✗ Schema is invalid: {error_count} error(s)"

        return ValidationReport(
            schema_valid=schema_valid,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            issues=self.issues,
            summary=summary
        )

    @staticmethod
    def _is_camel_case(s: str) -> bool:
        """Check if string is camelCase."""
        if not s:
            return False
        return s[0].islower() and "_" not in s

    @staticmethod
    def _check_nesting_depth(obj: Any, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth."""
        if not isinstance(obj, dict):
            return current_depth

        max_depth = current_depth

        for value in obj.values():
            if isinstance(value, dict):
                depth = ActionSchemaValidator._check_nesting_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)

        return max_depth


# =============================================================================
# Report Printing
# =============================================================================

def print_report(report: ValidationReport, verbose: bool = False):
    """Print validation report."""
    print(f"\n{'='*70}")
    print(f"OpenAPI Schema Validation Report")
    print(f"{'='*70}\n")

    print(f"Status: {report.summary}\n")

    print(f"Summary:")
    print(f"  Errors:   {report.error_count}")
    print(f"  Warnings: {report.warning_count}")
    print(f"  Info:     {report.info_count}")
    print(f"  Total:    {len(report.issues)}")

    if report.issues:
        print(f"\n{'-'*70}")
        print(f"Issues:")
        print(f"{'-'*70}\n")

        # Group by severity
        for severity in ["error", "warning", "info"]:
            issues = [i for i in report.issues if i.severity == severity]
            if not issues:
                continue

            severity_symbol = {
                "error": "✗",
                "warning": "⚠",
                "info": "ℹ"
            }[severity]

            print(f"{severity_symbol} {severity.upper()}: {len(issues)} issue(s)\n")

            for issue in issues:
                print(f"  Location: {issue.location}")
                print(f"  Issue: {issue.message}")
                print(f"  Fix: {issue.recommendation}")
                print()

    print(f"{'='*70}\n")

    if report.schema_valid:
        print("✓ Schema is ready for use with ChatGPT Actions")
    else:
        print("✗ Fix errors before using with ChatGPT Actions")

    print()


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Validate OpenAPI schemas for ChatGPT Actions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate schema
  python action_validator.py --schema weather_api.yaml

  # Verbose output
  python action_validator.py --schema weather_api.yaml --verbose

  # Save report to JSON
  python action_validator.py --schema weather_api.yaml --output report.json
        """
    )

    parser.add_argument(
        "--schema",
        type=str,
        required=True,
        help="Path to OpenAPI schema file (YAML or JSON)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save report to JSON file"
    )

    args = parser.parse_args()

    # Load schema
    try:
        with open(args.schema, 'r') as f:
            if args.schema.endswith('.yaml') or args.schema.endswith('.yml'):
                schema = yaml.safe_load(f)
            else:
                schema = json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file not found: {args.schema}")
        return 1
    except Exception as e:
        print(f"Error loading schema: {e}")
        return 1

    # Validate
    validator = ActionSchemaValidator(schema, verbose=args.verbose)
    report = validator.validate()

    # Print report
    print_report(report, verbose=args.verbose)

    # Save to JSON if requested
    if args.output:
        output_data = asdict(report)
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"✓ Report saved to: {args.output}\n")

    # Exit with appropriate code
    return 0 if report.schema_valid else 1


if __name__ == "__main__":
    exit(main())
