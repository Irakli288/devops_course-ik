"""Тесты расчета балансов, переводов и итогов по категориям."""

from splitter.models import Expense, Participant, Trip
from splitter.settlement import balances, totals_by_category, transfers


def make_trip():
    """Поездка из трех участников и двух расходов."""
    names = ["Анна", "Борис", "Вика"]
    trip = Trip("Тест", [Participant(n) for n in names])
    trip.expenses.append(Expense(9000, "Анна", names, "жилье"))
    trip.expenses.append(Expense(3000, "Борис", names, "еда"))
    return trip


def test_balances_sum_to_zero():
    """Сумма балансов всех участников равна нулю."""
    assert round(sum(balances(make_trip()).values()), 2) == 0


def test_transfers():
    """Должники переводят деньги тому, кто переплатил."""
    assert transfers(make_trip()) == [("Борис", "Анна", 1000.0),
                                      ("Вика", "Анна", 4000.0)]


def test_totals_by_category():
    """Расходы суммируются по категориям."""
    trip = make_trip()
    trip.expenses.append(Expense(1500, "Вика", ["Анна", "Вика"], "еда"))
    assert totals_by_category(trip) == {"жилье": 9000.0, "еда": 4500.0}
