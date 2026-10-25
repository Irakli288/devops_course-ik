"""Точка входа: демонстрация расчета расходов поездки."""

from splitter.models import Expense, Participant, Trip
from splitter.settlement import balances, transfers


def main():
    trip = Trip("Казань", [Participant("Анна"), Participant("Борис"),
                           Participant("Вика")])
    everyone = ["Анна", "Борис", "Вика"]
    trip.expenses.append(Expense(9000, "Анна", everyone, "жилье"))
    trip.expenses.append(Expense(3000, "Борис", everyone, "еда"))

    print(f"Поездка: {trip.name}")
    for name, value in balances(trip).items():
        print(f"  {name}: {value:+.2f} руб.")
    for debtor, creditor, amount in transfers(trip):
        print(f"  {debtor} -> {creditor}: {amount:.2f} руб.")


if __name__ == "__main__":
    main()
