# Сервис распределения расходов поездки

Учебный проект по дисциплине «Инструменты DevOps».

Приложение помогает группе людей, путешествующих вместе, учитывать общие
расходы поездки и честно делить их между участниками: считает долю каждого,
показывает балансы и формирует список переводов «кто → кому → сколько».

Документация проекта: [Wiki](https://github.com/Irakli288/devops_course-ik/wiki).
Задачи проекта: вкладка Issues и доска в Projects.

## Структура проекта

```
devops_course-ik/
├── README.md            # описание проекта
├── .gitignore           # исключения для git
├── .github/workflows/   # CI: Pylint и pytest (GitHub Actions)
├── requirements.txt     # зависимости Python
├── main.py              # точка входа (консольное приложение)
├── splitter/            # исходный код
│   ├── __init__.py
│   ├── models.py        # сущности: поездка, участник, расход
│   └── settlement.py    # расчет балансов, переводов и итогов по категориям
├── data/                # данные приложения (JSON)
│   └── .gitkeep
└── tests/               # автотесты pytest
    └── test_settlement.py
```

## Запуск

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
pytest
```
