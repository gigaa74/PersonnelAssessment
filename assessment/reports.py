from dataclasses import dataclass

from .scoring import Competency, Level


LABELS = {
    Competency.STRATEGIC_THINKING: "Стратегическое мышление",
    Competency.DELEGATION: "Делегирование",
    Competency.ACCOUNTABILITY: "Ответственность",
    Competency.COMMUNICATION: "Коммуникативные навыки",
    Competency.PERSISTENCE: "Настойчивость",
    Competency.RESULT_ORIENTATION: "Нацеленность на результат",
    Competency.MOTIVATION: "Мотивация",
    Competency.COMPOSURE: "Самообладание",
    Competency.MANAGEMENT: "Управленческая деятельность",
}
LEVEL_LABELS = {
    Level.VERY_LOW: "Очень низкий",
    Level.LOW: "Низкий",
    Level.MEDIUM: "Средний",
    Level.HIGH: "Высокий",
    Level.VERY_HIGH: "Очень высокий",
}
MANIFESTATIONS = {
    Competency.STRATEGIC_THINKING: "учёт долгосрочных последствий, взаимосвязей и нескольких сценариев",
    Competency.DELEGATION: "передача задач, выбор исполнителя и контроль без микроменеджмента",
    Competency.ACCOUNTABILITY: "выполнение договорённостей, признание ошибок и влияние на конечный итог",
    Competency.COMMUNICATION: "ясное изложение, слушание, обратная связь и работа с разногласиями",
    Competency.PERSISTENCE: "продолжение работы при препятствиях и поиск альтернативных способов",
    Competency.RESULT_ORIENTATION: "фокус на измеримом итоге, приоритетах и контроле прогресса",
    Competency.MOTIVATION: "внутренняя вовлечённость, инициативность и стремление развиваться",
    Competency.COMPOSURE: "устойчивость под давлением и управление реакциями в сложных разговорах",
    Competency.MANAGEMENT: "постановка задач, организация команды, обратная связь и управленческие решения",
}
PRACTICES = {
    Competency.STRATEGIC_THINKING: "Перед важными решениями фиксировать 2–3 сценария, риски и последствия на горизонте нескольких месяцев.",
    Competency.DELEGATION: "Передавать результат и полномочия вместе с критериями готовности и заранее согласованными контрольными точками.",
    Competency.ACCOUNTABILITY: "Заранее фиксировать обязательства, рано сообщать о рисках и завершать разбор ошибки конкретным планом действий.",
    Competency.COMMUNICATION: "Проверять понимание, отделять факты от интерпретаций и чаще использовать уточняющие вопросы.",
    Competency.PERSISTENCE: "Разбивать сложную цель на короткие этапы и после препятствия определять следующий шаг и срок.",
    Competency.RESULT_ORIENTATION: "Для каждой задачи формулировать измеримый итог и регулярно убирать действия, которые на него почти не влияют.",
    Competency.MOTIVATION: "Выбирать конкретную развивающую задачу на каждый рабочий цикл и фиксировать собственные инициативы.",
    Competency.COMPOSURE: "Использовать короткую паузу перед реакцией, возвращаться к фактам и планировать восстановление после перегрузки.",
    Competency.MANAGEMENT: "Согласовывать с командой результат, роли и сроки, а обратную связь давать до того, как отклонение станет критичным.",
}


@dataclass(frozen=True, slots=True)
class ReportRow:
    competency: Competency
    label: str
    percentage: int
    level: Level
    level_label: str
    interpretation: str
    recommendation: str


def _interpretation(competency, percentage, level):
    area = MANIFESTATIONS[competency]
    if level in {Level.VERY_HIGH, Level.HIGH}:
        return f"Показатель отражает выраженную тенденцию проявлять в работе {area}. Это вероятная рабочая сильная сторона, но её проявление зависит от контекста и условий задачи."
    if level is Level.MEDIUM:
        return f"Показатель отражает ситуативное проявление таких моделей поведения, как {area}. В привычных условиях они могут проявляться устойчиво, а при высокой нагрузке — менее последовательно."
    return f"Показатель отражает менее устойчивое проявление таких моделей поведения, как {area}. Это зона возможного развития, а не вывод о профессиональной пригодности человека."


def build_report(result_rows):
    rows = []
    for result in result_rows:
        competency = Competency(result.competency)
        level = Level(result.level)
        rows.append(ReportRow(
            competency=competency,
            label=LABELS[competency],
            percentage=result.percentage,
            level=level,
            level_label=LEVEL_LABELS[level],
            interpretation=_interpretation(competency, result.percentage, level),
            recommendation=PRACTICES[competency],
        ))
    rows.sort(key=lambda row: list(Competency).index(row.competency))
    ranked = sorted(rows, key=lambda row: (row.percentage, row.label))
    return {"rows": rows, "development": ranked[:3], "strengths": list(reversed(ranked[-3:]))}

