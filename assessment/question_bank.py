from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .scoring import Competency, ScoringItem


BANK_VERSION: Final = "2.0.0-pilot"
ANSWER_SCALE: Final = (
    "Совершенно не согласен",
    "Скорее не согласен",
    "Зависит от ситуации",
    "Скорее согласен",
    "Полностью согласен",
)


@dataclass(frozen=True, slots=True)
class Question:
    id: str
    text: str
    competency: Competency
    reverse_keyed: bool = False
    kind: str = "behavioral"
    weight: int = 1

    def scoring_item(self) -> ScoringItem:
        return ScoringItem(self.id, self.competency, self.reverse_keyed, self.weight)


def _q(code, competency, entries):
    return tuple(
        Question(f"{code}{index:02}", text, competency, reverse, kind)
        for index, (text, reverse, kind) in enumerate(entries, 1)
    )


QUESTIONS: Final = (
    *_q("ST", Competency.STRATEGIC_THINKING, (
        ("Перед важным решением я оцениваю, как оно повлияет на работу через несколько месяцев.", False, "behavioral"),
        ("Когда исходные данные неполны, я формулирую несколько возможных сценариев развития ситуации.", False, "situational"),
        ("При выборе между срочной и важной задачей я учитываю последствия откладывания каждой из них.", False, "situational"),
        ("Мне удобнее решать отдельные проблемы по мере появления, не связывая их с общей картиной.", True, "behavioral"),
        ("Если план работает сейчас, я редко проверяю, какие новые риски он может создать позднее.", True, "behavioral"),
        ("Предлагая изменение, я проверяю его влияние на клиентов, команду, ресурсы и смежные процессы.", False, "situational"),
    )),
    *_q("DL", Competency.DELEGATION, (
        ("Передавая задачу, я объясняю ожидаемый результат, ограничения и срок, оставляя исполнителю выбор способа.", False, "behavioral"),
        ("При высокой загрузке я выбираю исполнителя по его компетенциям и доступности, а не только по привычке.", False, "situational"),
        ("После передачи задачи я заранее договариваюсь о контрольных точках.", False, "behavioral"),
        ("Критически важную работу безопаснее выполнить самому, даже если сотрудник способен с ней справиться.", True, "situational"),
        ("Я часто уточняю каждый промежуточный шаг, даже когда результат и срок уже согласованы.", True, "behavioral"),
        ("Я использую подходящие задачи как возможность расширить самостоятельность сотрудника.", False, "behavioral"),
    )),
    *_q("AC", Competency.ACCOUNTABILITY, (
        ("Если результат оказался хуже ожидаемого, я сначала анализирую собственные решения и действия.", False, "behavioral"),
        ("Обнаружив свою ошибку, я сообщаю о ней тем, кого она затрагивает, и предлагаю исправление.", False, "situational"),
        ("Если срок под угрозой, я предупреждаю заранее и согласовываю новый план.", False, "situational"),
        ("Когда задаче мешают внешние обстоятельства, итог в основном зависит уже не от моих действий.", True, "behavioral"),
        ("Небольшое отклонение от договорённости можно не обсуждать, если его никто не заметил.", True, "situational"),
        ("Я проверяю, что взятые мной обязательства зафиксированы и доведены до результата.", False, "behavioral"),
    )),
    *_q("CM", Competency.COMMUNICATION, (
        ("Объясняя сложную задачу, я проверяю, одинаково ли мы понимаем ожидаемый результат.", False, "behavioral"),
        ("В споре я сначала уточняю аргументы собеседника, прежде чем защищать свою позицию.", False, "situational"),
        ("Я адаптирую объём деталей и терминологию к опыту человека, с которым говорю.", False, "behavioral"),
        ("Если моя мысль кажется мне ясной, дополнительная проверка понимания обычно не нужна.", True, "behavioral"),
        ("Когда обратная связь неприятна, я чаще объясняю свою позицию, чем задаю уточняющие вопросы.", True, "situational"),
        ("В сложном разговоре я отделяю наблюдаемые факты от своих выводов и оценок.", False, "situational"),
    )),
    *_q("PS", Competency.PERSISTENCE, (
        ("После отказа я выясняю причину и выбираю другой способ продвинуть задачу.", False, "situational"),
        ("Для длительной задачи я задаю промежуточные этапы и регулярно сверяю прогресс.", False, "behavioral"),
        ("Если первый подход не сработал, я пробую альтернативу, сохраняя цель.", False, "situational"),
        ("Несколько неудачных попыток обычно означают, что задачу лучше отложить без нового плана.", True, "behavioral"),
        ("Когда продвижение зависит от других людей, я предпочитаю ждать, пока ситуация прояснится сама.", True, "situational"),
        ("Столкнувшись с препятствием, я определяю следующий конкретный шаг и срок.", False, "behavioral"),
    )),
    *_q("RO", Competency.RESULT_ORIENTATION, (
        ("В начале работы я формулирую проверяемый результат, а не только перечень действий.", False, "behavioral"),
        ("При конкурирующих задачах я сначала выбираю те, которые сильнее влияют на итоговую цель.", False, "situational"),
        ("Я регулярно сопоставляю фактический прогресс с ожидаемым результатом.", False, "behavioral"),
        ("Если процесс выполнен правильно, недостигнутый итог не всегда требует пересмотра моих действий.", True, "behavioral"),
        ("Я могу долго улучшать детали, даже когда они уже почти не влияют на конечный результат.", True, "situational"),
        ("Когда срок ограничен, я принимаю обоснованное решение и фиксирую оставшиеся риски.", False, "situational"),
    )),
    *_q("MO", Competency.MOTIVATION, (
        ("Я самостоятельно ищу знания, которые помогут лучше выполнять текущую работу.", False, "behavioral"),
        ("Если появляется новая сложная задача, я стараюсь понять, чему она может меня научить.", False, "situational"),
        ("Я предлагаю улучшения, даже когда это не является отдельным поручением.", False, "behavioral"),
        ("Без внешнего контроля мне трудно поддерживать темп в длительных задачах.", True, "behavioral"),
        ("Если работа выполняется на приемлемом уровне, я редко ищу способы повысить мастерство.", True, "behavioral"),
        ("После достижения цели я определяю следующий профессиональный ориентир.", False, "behavioral"),
    )),
    *_q("CP", Competency.COMPOSURE, (
        ("Под давлением я делаю паузу, уточняю факты и только затем принимаю решение.", False, "situational"),
        ("В конфликте я способен сохранять рабочий тон, даже если собеседник говорит эмоционально.", False, "situational"),
        ("После неудачи я возвращаюсь к продуктивной работе без длительного снижения темпа.", False, "behavioral"),
        ("При резкой критике моя первая реакция часто определяет весь дальнейший разговор.", True, "behavioral"),
        ("Высокая нагрузка заметно влияет на то, как я разговариваю с коллегами.", True, "behavioral"),
        ("Когда одновременно возникает несколько проблем, я последовательно определяю приоритеты.", False, "situational"),
    )),
    *_q("MG", Competency.MANAGEMENT, (
        ("Ставя задачу команде, я определяю результат, полномочия, срок и критерии готовности.", False, "behavioral"),
        ("Если сотрудники расходятся во мнениях, я помогаю зафиксировать предмет разногласия и решение.", False, "situational"),
        ("Я даю обратную связь достаточно быстро, чтобы сотрудник мог скорректировать работу.", False, "behavioral"),
        ("За результат команды прежде всего отвечают исполнители своих отдельных задач.", True, "behavioral"),
        ("Развитие сотрудников имеет смысл обсуждать только при заметных проблемах в работе.", True, "behavioral"),
        ("Перед управленческим решением я учитываю возможности команды и последствия для общей нагрузки.", False, "situational"),
    )),
)


def scoring_items() -> tuple[ScoringItem, ...]:
    return tuple(question.scoring_item() for question in QUESTIONS)


def validate_bank() -> tuple[str, ...]:
    errors = []
    if len(QUESTIONS) != 54:
        errors.append(f"expected 54 questions, got {len(QUESTIONS)}")
    ids = [question.id for question in QUESTIONS]
    if len(ids) != len(set(ids)):
        errors.append("question identifiers must be unique")
    forbidden = {
        "стратегическое мышление", "делегирование", "ответственность",
        "коммуникативные навыки", "настойчивость", "нацеленность на результат",
        "мотивация", "самообладание", "управленческая деятельность",
    }
    for competency in Competency:
        group = [q for q in QUESTIONS if q.competency == competency]
        if len(group) != 6:
            errors.append(f"{competency}: expected 6 questions, got {len(group)}")
        reverse_count = sum(q.reverse_keyed for q in group)
        if reverse_count < 2:
            errors.append(f"{competency}: expected at least 2 reverse-keyed questions")
        if not {q.kind for q in group} >= {"behavioral", "situational"}:
            errors.append(f"{competency}: both item kinds are required")
    for question in QUESTIONS:
        lowered = question.text.casefold()
        if any(term in lowered for term in forbidden):
            errors.append(f"{question.id}: competency name is exposed")
        if question.weight < 1:
            errors.append(f"{question.id}: invalid weight")
    return tuple(errors)
