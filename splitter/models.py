"""Основные сущности предметной области."""

from dataclasses import dataclass, field


@dataclass
class Participant:
    name: str


@dataclass
class Expense:
    amount: float
    payer: str
    shared_by: list[str]
    category: str = "прочее"


@dataclass
class Trip:
    name: str
    participants: list[Participant] = field(default_factory=list)
    expenses: list[Expense] = field(default_factory=list)
