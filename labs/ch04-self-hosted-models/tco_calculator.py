#!/usr/bin/env python3
"""
Self-Hosted vs API Total Cost of Ownership (TCO) Calculator

This lab helps determine when self-hosting LLMs becomes cost-effective compared
to commercial APIs by calculating:
- API costs at different usage levels
- Self-hosted infrastructure costs (hardware, power, devops)
- Break-even analysis
- ROI projections

Supports multiple scenarios:
- Cloud GPU (AWS/GCP)
- On-premises datacenter
- Consumer hardware (development/edge)

Usage:
    # Basic calculation
    python tco_calculator.py --tokens-per-month 500M

    # Detailed comparison
    python tco_calculator.py --tokens-per-month 10B --api-cost 0.002 --deployment cloud

    # Generate cost projection report
    python tco_calculator.py --tokens-per-month 1B --months 36 --output tco_report.json

References:
    Patterson et al. (2023): "Carbon Emissions and Large Neural Network Training"
    Chapter 4, Section 4.8: Cost Analysis
"""

import argparse
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt


@dataclass
class APICosts:
    """Commercial API cost structure."""
    provider: str
    cost_per_1k_tokens: float
    typical_latency_ms: int
    rate_limits: str


@dataclass
class HardwareConfig:
    """Self-hosted hardware configuration."""
    name: str
    gpu_model: str
    gpu_count: int
    gpu_cost_each: float
    cpu_cost: float
    ram_cost: float
    storage_cost: float
    total_upfront_cost: float


@dataclass
class OperatingCosts:
    """Monthly operating costs for self-hosted."""
    cloud_compute: float
    colocation: float
    power_kwh: float
    power_cost_per_kwh: float
    power_monthly: float
    devops_fte: float
    devops_monthly: float
    total_monthly: float


@dataclass
class TCOResult:
    """Total Cost of Ownership result."""
    scenario: str
    tokens_per_month: int
    api_cost_monthly: float
    self_hosted_upfront: float
    self_hosted_monthly: float
    self_hosted_amortized_monthly: float  # Upfront / 36 months
    break_even_months: float
    roi_12_months: float
    roi_36_months: float


# =============================================================================
# Cost Data (from Chapter 4)
# =============================================================================

API_PROVIDERS = {
    "gpt-3.5-turbo": APICosts("OpenAI GPT-3.5", 0.002, 500, "10K RPM"),
    "gpt-4": APICosts("OpenAI GPT-4", 0.03, 800, "500 RPM"),
    "claude-3-sonnet": APICosts("Anthropic Claude 3 Sonnet", 0.015, 400, "5K RPM"),
    "claude-3-opus": APICosts("Anthropic Claude 3 Opus", 0.075, 600, "1K RPM"),
}

HARDWARE_CONFIGS = {
    "consumer_rtx4090": HardwareConfig(
        name="Consumer RTX 4090",
        gpu_model="RTX 4090",
        gpu_count=1,
        gpu_cost_each=1_599,
        cpu_cost=500,
        ram_cost=200,
        storage_cost=300,
        total_upfront_cost=2_599,
    ),
    "datacenter_a100_single": HardwareConfig(
        name="Datacenter 1× A100",
        gpu_model="A100 80GB",
        gpu_count=1,
        gpu_cost_each=15_000,
        cpu_cost=2_000,
        ram_cost=1_000,
        storage_cost=1_000,
        total_upfront_cost=19_000,
    ),
    "datacenter_a100_dual": HardwareConfig(
        name="Datacenter 2× A100",
        gpu_model="A100 80GB",
        gpu_count=2,
        gpu_cost_each=15_000,
        cpu_cost=3_000,
        ram_cost=2_000,
        storage_cost=1_500,
        total_upfront_cost=36_500,
    ),
}


# =============================================================================
# TCO Calculator
# =============================================================================

class TCOCalculator:
    """Calculate Total Cost of Ownership for self-hosted vs API."""

    def __init__(
        self,
        tokens_per_month: int,
        api_provider: str = "gpt-3.5-turbo",
        hardware_config: str = "datacenter_a100_single",
        deployment: str = "cloud",  # cloud, colocation, on-prem
        amortization_months: int = 36,
    ):
        self.tokens_per_month = tokens_per_month
        self.api_costs = API_PROVIDERS[api_provider]
        self.hardware = HARDWARE_CONFIGS[hardware_config]
        self.deployment = deployment
        self.amortization_months = amortization_months

    def calculate_api_costs(self) -> float:
        """Calculate monthly API costs."""
        tokens_in_1k = self.tokens_per_month / 1_000
        return tokens_in_1k * self.api_costs.cost_per_1k_tokens

    def calculate_cloud_costs(self) -> OperatingCosts:
        """Calculate cloud deployment costs (AWS/GCP)."""
        # AWS p4d.24xlarge: 8× A100 = ~$32/hour = $23,040/month
        # Scale down based on GPU count
        cloud_compute_monthly = 2_400 * self.hardware.gpu_count

        return OperatingCosts(
            cloud_compute=cloud_compute_monthly,
            colocation=0,
            power_kwh=0,  # Included in cloud
            power_cost_per_kwh=0,
            power_monthly=0,
            devops_fte=0.2,  # 20% FTE for management
            devops_monthly=3_000,  # $15K/month × 0.2
            total_monthly=cloud_compute_monthly + 3_000,
        )

    def calculate_colocation_costs(self) -> OperatingCosts:
        """Calculate colocation deployment costs."""
        # Colocation: $200-500/month per server
        colo_monthly = 300

        # Power: GPU TDP (400W each) + CPU (200W) + overhead (30%)
        power_watts = (self.hardware.gpu_count * 400) + 200
        power_watts_with_overhead = power_watts * 1.3
        power_kwh_monthly = (power_watts_with_overhead / 1000) * 24 * 30
        power_cost_monthly = power_kwh_monthly * 0.12  # $0.12/kWh

        return OperatingCosts(
            cloud_compute=0,
            colocation=colo_monthly,
            power_kwh=power_kwh_monthly,
            power_cost_per_kwh=0.12,
            power_monthly=power_cost_monthly,
            devops_fte=0.3,  # 30% FTE
            devops_monthly=4_500,
            total_monthly=colo_monthly + power_cost_monthly + 4_500,
        )

    def calculate_onprem_costs(self) -> OperatingCosts:
        """Calculate on-premises deployment costs."""
        # Power only (no colo fees, assuming existing datacenter)
        power_watts = (self.hardware.gpu_count * 400) + 200
        power_watts_with_overhead = power_watts * 1.3
        power_kwh_monthly = (power_watts_with_overhead / 1000) * 24 * 30
        power_cost_monthly = power_kwh_monthly * 0.10  # $0.10/kWh (datacenter rate)

        return OperatingCosts(
            cloud_compute=0,
            colocation=0,
            power_kwh=power_kwh_monthly,
            power_cost_per_kwh=0.10,
            power_monthly=power_cost_monthly,
            devops_fte=0.15,  # 15% FTE (shared SRE team)
            devops_monthly=2_250,
            total_monthly=power_cost_monthly + 2_250,
        )

    def calculate_operating_costs(self) -> OperatingCosts:
        """Calculate monthly operating costs based on deployment type."""
        if self.deployment == "cloud":
            return self.calculate_cloud_costs()
        elif self.deployment == "colocation":
            return self.calculate_colocation_costs()
        else:  # on-prem
            return self.calculate_onprem_costs()

    def calculate_tco(self) -> TCOResult:
        """Calculate full TCO comparison."""
        api_monthly = self.calculate_api_costs()
        operating = self.calculate_operating_costs()

        # Amortize hardware cost over period (typically 36 months)
        hardware_amortized_monthly = self.hardware.total_upfront_cost / self.amortization_months

        # Total self-hosted monthly cost (amortized hardware + operating)
        self_hosted_monthly_total = hardware_amortized_monthly + operating.total_monthly

        # Break-even calculation
        # api_monthly × N = hardware_upfront + (operating_monthly × N)
        # api_monthly × N - operating_monthly × N = hardware_upfront
        # N × (api_monthly - operating_monthly) = hardware_upfront
        # N = hardware_upfront / (api_monthly - operating_monthly)

        monthly_savings = api_monthly - operating.total_monthly

        if monthly_savings > 0:
            break_even = self.hardware.total_upfront_cost / monthly_savings
        else:
            break_even = float('inf')  # Never breaks even

        # ROI calculation
        def calculate_roi(months: int) -> float:
            api_total = api_monthly * months
            self_hosted_total = self.hardware.total_upfront_cost + (operating.total_monthly * months)
            savings = api_total - self_hosted_total
            roi = (savings / self_hosted_total) * 100 if self_hosted_total > 0 else 0
            return roi

        roi_12 = calculate_roi(12)
        roi_36 = calculate_roi(36)

        return TCOResult(
            scenario=f"{self.deployment}-{self.hardware.name}",
            tokens_per_month=self.tokens_per_month,
            api_cost_monthly=api_monthly,
            self_hosted_upfront=self.hardware.total_upfront_cost,
            self_hosted_monthly=operating.total_monthly,
            self_hosted_amortized_monthly=self_hosted_monthly_total,
            break_even_months=break_even,
            roi_12_months=roi_12,
            roi_36_months=roi_36,
        )

    def print_report(self, result: TCOResult):
        """Print TCO report."""
        print(f"\n{'='*70}")
        print(f"Total Cost of Ownership (TCO) Analysis")
        print(f"{'='*70}\n")

        print(f"Scenario: {result.scenario}")
        print(f"Usage: {result.tokens_per_month:,} tokens/month")
        print(f"        ({result.tokens_per_month/1e9:.2f}B tokens/month)")

        print(f"\n{'-'*70}")
        print(f"Commercial API Costs")
        print(f"{'-'*70}")
        print(f"Provider: {self.api_costs.provider}")
        print(f"Rate: ${self.api_costs.cost_per_1k_tokens}/1K tokens")
        print(f"Monthly cost: ${result.api_cost_monthly:,.2f}")
        print(f"Annual cost: ${result.api_cost_monthly * 12:,.2f}")

        print(f"\n{'-'*70}")
        print(f"Self-Hosted Costs")
        print(f"{'-'*70}")
        print(f"Hardware: {self.hardware.name}")
        print(f"  - GPUs: {self.hardware.gpu_count}× {self.hardware.gpu_model}")
        print(f"  - Upfront cost: ${self.hardware.total_upfront_cost:,.2f}")
        print(f"  - Amortized ({self.amortization_months} months): ${result.self_hosted_upfront / self.amortization_months:,.2f}/month")

        operating = self.calculate_operating_costs()
        print(f"\nOperating costs ({self.deployment} deployment):")
        if operating.cloud_compute > 0:
            print(f"  - Cloud compute: ${operating.cloud_compute:,.2f}/month")
        if operating.colocation > 0:
            print(f"  - Colocation: ${operating.colocation:,.2f}/month")
        if operating.power_monthly > 0:
            print(f"  - Power ({operating.power_kwh:.0f} kWh): ${operating.power_monthly:,.2f}/month")
        print(f"  - DevOps ({operating.devops_fte:.1%} FTE): ${operating.devops_monthly:,.2f}/month")
        print(f"  - Total operating: ${operating.total_monthly:,.2f}/month")

        print(f"\nTotal monthly (amortized): ${result.self_hosted_amortized_monthly:,.2f}")
        print(f"Annual cost (Year 1): ${self.hardware.total_upfront_cost + (operating.total_monthly * 12):,.2f}")

        print(f"\n{'-'*70}")
        print(f"Comparison")
        print(f"{'-'*70}")

        monthly_diff = result.api_cost_monthly - result.self_hosted_amortized_monthly
        annual_diff = monthly_diff * 12

        if result.break_even_months < float('inf'):
            print(f"Break-even point: {result.break_even_months:.1f} months")
            print(f"Monthly savings (after break-even): ${abs(monthly_diff):,.2f}")
            print(f"Annual savings (amortized): ${annual_diff:,.2f}")
            print(f"ROI (12 months): {result.roi_12_months:.1f}%")
            print(f"ROI (36 months): {result.roi_36_months:.1f}%")
        else:
            print(f"❌ Self-hosting NOT cost-effective at this usage level")
            print(f"Monthly loss: ${abs(monthly_diff):,.2f}")
            print(f"Annual loss: ${abs(annual_diff):,.2f}")

        print(f"\n{'-'*70}")
        print(f"Recommendation")
        print(f"{'-'*70}\n")

        self._print_recommendation(result)

        print(f"\n{'='*70}\n")

    def _print_recommendation(self, result: TCOResult):
        """Print recommendation based on TCO analysis."""
        if result.break_even_months < 12:
            print(f"✓ STRONGLY RECOMMEND self-hosting")
            print(f"  Break-even in <1 year ({result.break_even_months:.1f} months)")
            print(f"  ROI: {result.roi_12_months:.1f}% in 12 months")
        elif result.break_even_months < 24:
            print(f"✓ RECOMMEND self-hosting")
            print(f"  Break-even in {result.break_even_months:.1f} months")
            print(f"  Positive ROI over typical hardware lifecycle (36 months)")
        elif result.break_even_months < 36:
            print(f"○ CONSIDER self-hosting")
            print(f"  Break-even near end of hardware lifecycle ({result.break_even_months:.1f} months)")
            print(f"  Benefits: Data privacy, customization, no rate limits")
        else:
            print(f"✗ NOT RECOMMENDED for self-hosting")
            print(f"  Usage too low ({self.tokens_per_month/1e9:.2f}B tokens/month)")
            print(f"  Stick with API or consider:")
            print(f"    - Smaller model (7B vs 70B)")
            print(f"    - Cheaper hardware (consumer GPU)")
            print(f"    - Shared infrastructure")

        # Additional considerations
        print(f"\nAdditional factors to consider:")
        if result.tokens_per_month > 10e9:  # >10B tokens/month
            print(f"  + High usage volume favors self-hosting")
        print(f"  + Data privacy requirements may override cost considerations")
        print(f"  + Customization (fine-tuning) easier with self-hosted")
        if self.deployment == "cloud":
            print(f"  - Cloud deployment has minimal upfront commitment")


# =============================================================================
# Scenario Analysis
# =============================================================================

def run_scenario_analysis():
    """Run multiple scenarios and compare."""
    scenarios = [
        (500_000_000, "gpt-3.5-turbo", "datacenter_a100_single", "cloud"),      # 500M tokens
        (1_000_000_000, "gpt-3.5-turbo", "datacenter_a100_single", "cloud"),    # 1B tokens
        (5_000_000_000, "gpt-3.5-turbo", "datacenter_a100_single", "cloud"),    # 5B tokens
        (10_000_000_000, "gpt-3.5-turbo", "datacenter_a100_dual", "cloud"),     # 10B tokens
    ]

    results = []

    for tokens, api, hardware, deployment in scenarios:
        calc = TCOCalculator(
            tokens_per_month=tokens,
            api_provider=api,
            hardware_config=hardware,
            deployment=deployment,
        )
        result = calc.calculate_tco()
        results.append(result)

    # Print comparison table
    print(f"\n{'='*70}")
    print(f"Multi-Scenario Comparison")
    print(f"{'='*70}\n")

    print(f"{'Tokens/Month':<15} {'API Cost':<12} {'Self-Hosted':<15} {'Break-Even':<12} {'Recommend':<15}")
    print(f"{'':=<15} {'':=<12} {'':=<15} {'':=<12} {'':=<15}")

    for r in results:
        tokens_formatted = f"{r.tokens_per_month/1e9:.1f}B"
        api_formatted = f"${r.api_cost_monthly:,.0f}"
        self_formatted = f"${r.self_hosted_amortized_monthly:,.0f}"
        breakeven_formatted = f"{r.break_even_months:.0f}mo" if r.break_even_months < 100 else "Never"

        if r.break_even_months < 12:
            recommend = "✓ Yes"
        elif r.break_even_months < 24:
            recommend = "○ Maybe"
        else:
            recommend = "✗ No"

        print(f"{tokens_formatted:<15} {api_formatted:<12} {self_formatted:<15} {breakeven_formatted:<12} {recommend:<15}")

    print(f"\n{'='*70}\n")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Self-Hosted vs API TCO Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic calculation (500M tokens/month)
  python tco_calculator.py --tokens-per-month 500M

  # High-volume scenario (10B tokens/month)
  python tco_calculator.py --tokens-per-month 10B --hardware datacenter_a100_dual

  # Compare deployment types
  python tco_calculator.py --tokens-per-month 1B --deployment colocation

  # Multi-scenario analysis
  python tco_calculator.py --scenario-analysis

  # Generate report
  python tco_calculator.py --tokens-per-month 5B --output tco_report.json

Deployment types:
  - cloud: AWS/GCP cloud GPU instances
  - colocation: Owned hardware in colocation facility
  - on-prem: Owned hardware in existing datacenter
        """,
    )

    parser.add_argument(
        "--tokens-per-month",
        type=str,
        help="Tokens per month (e.g., 500M, 1B, 10B)",
    )
    parser.add_argument(
        "--api-provider",
        type=str,
        default="gpt-3.5-turbo",
        choices=list(API_PROVIDERS.keys()),
        help="API provider (default: gpt-3.5-turbo)",
    )
    parser.add_argument(
        "--hardware",
        type=str,
        default="datacenter_a100_single",
        choices=list(HARDWARE_CONFIGS.keys()),
        help="Hardware configuration (default: datacenter_a100_single)",
    )
    parser.add_argument(
        "--deployment",
        type=str,
        default="cloud",
        choices=["cloud", "colocation", "on-prem"],
        help="Deployment type (default: cloud)",
    )
    parser.add_argument(
        "--amortization-months",
        type=int,
        default=36,
        help="Hardware amortization period (default: 36 months)",
    )
    parser.add_argument(
        "--scenario-analysis",
        action="store_true",
        help="Run multi-scenario analysis",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save results to JSON file",
    )

    args = parser.parse_args()

    if args.scenario_analysis:
        run_scenario_analysis()
        return

    if not args.tokens_per_month:
        parser.error("--tokens-per-month required (or use --scenario-analysis)")

    # Parse tokens (supports M/B suffix)
    tokens_str = args.tokens_per_month.upper()
    if tokens_str.endswith('B'):
        tokens = int(float(tokens_str[:-1]) * 1_000_000_000)
    elif tokens_str.endswith('M'):
        tokens = int(float(tokens_str[:-1]) * 1_000_000)
    else:
        tokens = int(tokens_str)

    # Calculate TCO
    calculator = TCOCalculator(
        tokens_per_month=tokens,
        api_provider=args.api_provider,
        hardware_config=args.hardware,
        deployment=args.deployment,
        amortization_months=args.amortization_months,
    )

    result = calculator.calculate_tco()
    calculator.print_report(result)

    # Save to JSON if requested
    if args.output:
        output_data = {
            "parameters": {
                "tokens_per_month": tokens,
                "api_provider": args.api_provider,
                "hardware": args.hardware,
                "deployment": args.deployment,
            },
            "result": asdict(result),
        }

        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"✓ Results saved to: {args.output}\n")


if __name__ == "__main__":
    main()
