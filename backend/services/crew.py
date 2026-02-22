"""CrewAI Agentic Engine for FalconEye.

Defines the three core agents (Recon, Breach Analyst, Strategy) and
wires them into a sequential CrewAI process.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from crewai import Agent, Crew, Process, Task
from crewai_tools import SerperDevTool

from backend.memory.rag_pipeline import build_rag_tool
from backend.services.safety_filter import SafetyFilter

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #
safety = SafetyFilter()


# ------------------------------------------------------------------ #
# Agent Factories
# ------------------------------------------------------------------ #
def _build_recon_agent() -> Agent:
    search_tool = SerperDevTool()
    return Agent(
        role="Recon Agent",
        goal=(
            "Gather publicly available intelligence about the target "
            "using search engines and open-source data."
        ),
        backstory=(
            "You are an elite OSINT investigator with years of experience "
            "in passive reconnaissance. You never interact with the target "
            "directly and only use publicly available information."
        ),
        tools=[search_tool],
        verbose=True,
        allow_delegation=False,
    )


def _build_breach_analyst(pinecone_index: str | None = None) -> Agent:
    tools = []
    if pinecone_index:
        rag_tool = build_rag_tool(pinecone_index)
        tools.append(rag_tool)
    return Agent(
        role="Breach Analyst",
        goal=(
            "Correlate reconnaissance findings with historical breach data "
            "stored in the vector database to identify exposed credentials "
            "and leaked records."
        ),
        backstory=(
            "You are a seasoned threat-intelligence analyst who specialises "
            "in correlating breach dumps, paste-site leaks, and dark-web "
            "mentions with live OSINT findings."
        ),
        tools=tools,
        verbose=True,
        allow_delegation=False,
    )


def _build_strategy_agent() -> Agent:
    return Agent(
        role="Strategy Agent",
        goal=(
            "Using the combined OSINT and breach data, craft a realistic "
            "social-engineering simulation plan that highlights the target's "
            "exposure and recommends mitigations."
        ),
        backstory=(
            "You are a red-team consultant who designs phishing simulations "
            "and social-engineering exercises for Fortune-500 companies."
        ),
        verbose=True,
        allow_delegation=False,
    )


# ------------------------------------------------------------------ #
# Task Factories
# ------------------------------------------------------------------ #
def _recon_task(agent: Agent, target: str) -> Task:
    return Task(
        description=(
            f"Perform passive reconnaissance on the target: '{target}'. "
            "Search for social-media profiles, public records, corporate "
            "registrations, and any other open-source data."
        ),
        expected_output=(
            "A Markdown report with sections:\n"
            "## Discovered Resources\n"
            "For each finding list:\n"
            "- **Resource:** [Title]\n"
            "- **URL:** [Link]\n"
            "- **Info:** [Snippet or description]\n\n"
            "## Summary\n"
            "A brief summary of all discovered OSINT data points "
            "including URLs, usernames, and associated metadata."
        ),
        agent=agent,
    )


def _breach_task(agent: Agent, target: str) -> Task:
    return Task(
        description=(
            f"Analyse breach and leak databases for any records related "
            f"to the target: '{target}'. Cross-reference with the recon "
            "findings provided by the Recon Agent."
        ),
        expected_output=(
            "A Markdown correlation report with sections:\n"
            "## Breach Findings\n"
            "For each finding list:\n"
            "- **Resource:** [Breach name or source]\n"
            "- **URL:** [Reference link]\n"
            "- **Info:** [Breached credentials, exposed PII, or leak details]\n\n"
            "## Historical References\n"
            "A list of historical leak references and their relevance."
        ),
        agent=agent,
    )


def _strategy_task(agent: Agent, target: str) -> Task:
    return Task(
        description=(
            f"Based on all gathered intelligence for '{target}', design "
            "a social-engineering simulation plan. Include phishing "
            "pretexts, recommended attack vectors, and defensive "
            "mitigations the target should adopt."
        ),
        expected_output=(
            "A detailed social-engineering simulation report in Markdown "
            "format with sections:\n"
            "## Executive Summary\n"
            "## Attack Vectors\n"
            "For each vector list:\n"
            "- **Resource:** [Vector name]\n"
            "- **URL:** [Related link if applicable]\n"
            "- **Info:** [Description and impact]\n\n"
            "## Phishing Pretexts\n"
            "## Risk Rating\n"
            "## Mitigations"
        ),
        agent=agent,
    )


# ------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------ #
def build_crew(
    target: str,
    pinecone_index: str | None = None,
    step_callback: Callable[[Any], None] | None = None,
) -> Crew:
    """Assemble and return a FalconEye ``Crew`` ready for kick-off.

    Parameters
    ----------
    target:
        The OSINT target (company name, domain, or person).
    pinecone_index:
        Optional Pinecone index name for RAG-based breach correlation.
    step_callback:
        Optional callback invoked after each agent step – used to push
        live updates to the frontend via SSE.
    """
    safety.validate(target)

    recon = _build_recon_agent()
    analyst = _build_breach_analyst(pinecone_index)
    strategist = _build_strategy_agent()

    crew = Crew(
        agents=[recon, analyst, strategist],
        tasks=[
            _recon_task(recon, target),
            _breach_task(analyst, target),
            _strategy_task(strategist, target),
        ],
        process=Process.sequential,
        max_rpm=2,
        verbose=True,
        step_callback=step_callback,
    )
    return crew
