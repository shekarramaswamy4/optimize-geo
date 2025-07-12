#!/usr/bin/env python3
"""Command-line interface for LumaRank."""

import argparse
import asyncio
import json
import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.config.settings import Settings
from src.services.analyzer import WebsiteAnalyzerService
from src.utils.logging import setup_logging

console = Console()


def print_company_info(info: dict[str, Any]) -> None:
    """Print company information in a formatted way."""
    table = Table(title="Company Information", show_header=False, expand=True)
    table.add_column("Field", style="cyan", width=25)
    table.add_column("Value", style="white")
    
    table.add_row("Company Name", info.get("name", "Unknown"))
    table.add_row("Description", info.get("description", "N/A"))
    table.add_row("Target Customers", info.get("ideal_customer_profile", "N/A"))
    table.add_row("Industry", info.get("industry", "N/A") or "N/A")
    
    if info.get("key_features"):
        features = "\n".join(f"• {f}" for f in info["key_features"])
        table.add_row("Key Features", features)
    
    if info.get("pricing_info"):
        table.add_row("Pricing", info["pricing_info"])
    
    console.print(table)


def print_questions(questions: dict[str, list[dict[str, Any]]]) -> None:
    """Print generated questions."""
    console.print("\n[bold]Generated Search Questions[/bold]\n")
    
    # Company-specific questions
    if questions.get("company_specific"):
        console.print("[cyan]Company-Specific Questions:[/cyan]")
        for i, q in enumerate(questions["company_specific"], 1):
            console.print(f"  {i}. {q['question']}")
            console.print(f"     [dim]Intent: {q['intent']}[/dim]")
    
    # Problem-based questions
    if questions.get("problem_based"):
        console.print("\n[cyan]Problem-Based Questions:[/cyan]")
        for i, q in enumerate(questions["problem_based"], 1):
            console.print(f"  {i}. {q['question']}")
            console.print(f"     [dim]Intent: {q['intent']}[/dim]")


def print_test_results(results: list[dict[str, Any]], success_rate: float) -> None:
    """Print test results in a formatted table."""
    console.print("\n[bold]Question Test Results[/bold]\n")
    
    table = Table(show_header=True, expand=True)
    table.add_column("Question", style="cyan", width=40)
    table.add_column("Type", style="magenta", width=15)
    table.add_column("Score", style="yellow", width=10)
    table.add_column("Reason", style="white", width=35)
    
    for result in results:
        score_color = "red" if result["score"] == 0 else "yellow" if result["score"] == 1 else "green"
        table.add_row(
            result["question"][:40] + "..." if len(result["question"]) > 40 else result["question"],
            result["question_type"].replace("_", " ").title(),
            f"[{score_color}]{result['score']}/2[/{score_color}]",
            result["scoring_reason"],
        )
    
    console.print(table)
    
    # Success rate panel
    rate_color = "red" if success_rate < 0.5 else "yellow" if success_rate < 0.75 else "green"
    console.print(
        Panel(
            f"[{rate_color}]Overall Success Rate: {success_rate:.1%}[/{rate_color}]",
            title="Summary",
            expand=False,
        )
    )


async def analyze_website(url: str, company_name: str | None = None, test_questions: bool = True) -> None:
    """Analyze a website and display results."""
    settings = Settings()
    
    async with WebsiteAnalyzerService(settings) as analyzer:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Fetch website
            task = progress.add_task("Fetching website content...", total=None)
            try:
                content = await analyzer.fetch_website_content(url)
                progress.update(task, completed=True)
            except Exception as e:
                console.print(f"[red]Error fetching website: {e}[/red]")
                return
            
            # Analyze content
            task = progress.add_task("Analyzing content...", total=None)
            try:
                company_info = await analyzer.analyze_content(content)
                if company_name:
                    company_info.name = company_name
                progress.update(task, completed=True)
            except Exception as e:
                console.print(f"[red]Error analyzing content: {e}[/red]")
                return
            
            # Generate questions
            task = progress.add_task("Generating search questions...", total=None)
            try:
                questions = await analyzer.generate_search_questions(company_info)
                progress.update(task, completed=True)
            except Exception as e:
                console.print(f"[red]Error generating questions: {e}[/red]")
                return
            
            # Test questions if requested
            test_results = None
            success_rate = None
            
            if test_questions:
                task = progress.add_task("Testing questions...", total=None)
                try:
                    test_results, success_rate = await analyzer.test_all_questions(
                        questions, company_info.name
                    )
                    progress.update(task, completed=True)
                except Exception as e:
                    console.print(f"[red]Error testing questions: {e}[/red]")
                    return
        
        # Display results
        console.print("\n")
        print_company_info(company_info.model_dump())
        
        # Convert questions to dict format for display
        questions_dict = {
            "company_specific": [q.model_dump() for q in questions["company_specific"]],
            "problem_based": [q.model_dump() for q in questions["problem_based"]],
        }
        print_questions(questions_dict)
        
        if test_results:
            results_dict = [r.model_dump() for r in test_results]
            print_test_results(results_dict, success_rate)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze websites and generate customer search questions"
    )
    parser.add_argument(
        "url",
        nargs="?",
        default="https://spacetil.com",
        help="Website URL to analyze (default: https://spacetil.com)",
    )
    parser.add_argument(
        "--company-name",
        help="Override company name (otherwise extracted from URL)",
    )
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip testing the generated questions",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    if args.debug:
        import os
        os.environ["LOG_LEVEL"] = "DEBUG"
    
    setup_logging()
    
    # Validate URL
    if not args.url.startswith(("http://", "https://")):
        args.url = f"https://{args.url}"
    
    try:
        # Run the analysis
        if args.json:
            # For JSON output, we need to capture the results differently
            console.print("[yellow]JSON output not implemented yet[/yellow]")
        else:
            asyncio.run(
                analyze_website(
                    args.url,
                    args.company_name,
                    test_questions=not args.no_test,
                )
            )
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()