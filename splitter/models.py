"""Основные сущности предметной области."""

from dataclasses import dataclass, field


@dataclass
class Participant:
    """Участник поездки."""

    name: str


@dataclass
class Expense:
    """Расход: сумма, кто заплатил и на кого делится."""

    amount: float
    payer: str
    shared_by: list[str]
    category: str = "прочее"


@dataclass
class Trip:
    """Поездка со списком участников и расходов."""

    name: str
    participants: list[Participant] = field(default_factory=list)
    expenses: list[Expense] = field(default_factory=list)
