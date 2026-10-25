from splitter.models import Expense, Participant, Trip
from splitter.settlement import balances, transfers


def make_trip():
    names = ["Анна", "Борис", "Вика"]
    trip = Trip("Тест", [Participant(n) for n in names])
    trip.expenses.append(Expense(9000, "Анна", names))
    trip.expenses.append(Expense(3000, "Борис", names))
    return trip


def test_balances_sum_to_zero():
    assert round(sum(balances(make_trip()).values()), 2) == 0


def test_transfers():
    assert transfers(make_trip()) == [("Борис", "Анна", 1000.0),
                                      ("Вика", "Анна", 4000.0)]
