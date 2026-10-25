"""Расчет балансов участников и переводов между ними."""

from .models import Trip


def balances(trip: Trip) -> dict[str, float]:
    """Сколько каждый участник переплатил (+) или недоплатил (-)."""
    result = {p.name: 0.0 for p in trip.participants}
    for expense in trip.expenses:
        share = expense.amount / len(expense.shared_by)
        result[expense.payer] += expense.amount
        for name in expense.shared_by:
            result[name] -= share
    return {name: round(value, 2) for name, value in result.items()}


def transfers(trip: Trip) -> list[tuple[str, str, float]]:
    """Список переводов (кто, кому, сколько) для взаиморасчета."""
    debtors = [[n, -b] for n, b in balances(trip).items() if b < 0]
    creditors = [[n, b] for n, b in balances(trip).items() if b > 0]
    result = []
    while debtors and creditors:
        debtor, creditor = debtors[0], creditors[0]
        amount = round(min(debtor[1], creditor[1]), 2)
        result.append((debtor[0], creditor[0], amount))
        debtor[1] -= amount
        creditor[1] -= amount
        if debtor[1] < 0.01:
            debtors.pop(0)
        if creditor[1] < 0.01:
            creditors.pop(0)
    return result


def totals_by_category(trip: Trip) -> dict[str, float]:
    """Сумма расходов поездки по каждой категории."""
    result: dict[str, float] = {}
    for expense in trip.expenses:
        result[expense.category] = result.get(expense.category, 0.0) + expense.amount
    return {category: round(value, 2) for category, value in result.items()}
