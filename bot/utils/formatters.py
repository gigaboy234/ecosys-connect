from bot.database.models import Partner, Startup, StartupStage, Student, Teacher

_STAGE_LABELS = {
    StartupStage.idea: "💡 Идея",
    StartupStage.mvp: "🛠 MVP",
    StartupStage.prototype: "🔬 Прототип",
    StartupStage.scaling: "📈 Масштабирование",
}

_GOAL_LABELS = {
    "find_startup": "Ищу стартап",
    "create_startup": "Хочу создать стартап",
    "find_teacher": "Хочу найти преподавателя",
}

_FORMAT_LABELS = {
    "offline": "Очно",
    "online": "Онлайн",
    "mixed": "Смешанно",
}


def fmt_student(s: Student) -> str:
    tags = " | ".join(s.directions) if s.directions else "—"
    skills = ", ".join(s.skills) if s.skills else "—"
    portfolio = s.portfolio or "—"
    goal = _GOAL_LABELS.get(s.goal.value if hasattr(s.goal, "value") else s.goal, s.goal)
    return (
        f"🎓 <b>{s.name} {s.surname}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏫 {s.university}, {s.year} курс\n"
        f"📚 Факультет: {s.faculty}\n"
        f"🏷 Направления: {tags}\n"
        f"🔧 Навыки: {skills}\n"
        f"🔗 Портфолио: {portfolio}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 {s.description}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Цель: {goal}"
    )


def fmt_startup(s: Startup) -> str:
    tags = " | ".join(s.tags) if s.tags else "—"
    needs = ", ".join(s.needs) if s.needs else "—"
    stage = _STAGE_LABELS.get(s.stage, str(s.stage))
    return (
        f"🚀 <b>{s.name}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 {s.description}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏷 Теги: {tags}\n"
        f"📊 Стадия: {stage}\n"
        f"🤝 Нужны: {needs}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📞 Контакт: {s.contact}"
    )


def fmt_teacher(t: Teacher) -> str:
    dirs = " | ".join(t.research_directions) if t.research_directions else "—"
    comp = ", ".join(t.competencies) if t.competencies else "—"
    help_t = ", ".join(t.help_types) if t.help_types else "—"
    fmt = _FORMAT_LABELS.get(t.format.value if hasattr(t.format, "value") else t.format, str(t.format))
    return (
        f"👨‍🏫 <b>{t.full_name}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎓 {t.degree}\n"
        f"🏛 {t.department}\n"
        f"🔬 Направления: {dirs}\n"
        f"💡 Компетенции: {comp}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🤝 Помогу с: {help_t}\n"
        f"⏱ Доступность: {t.availability} ч/нед\n"
        f"📍 Формат: {fmt}"
    )


def fmt_partner(p: Partner) -> str:
    needs = ", ".join(p.needs) if p.needs else "—"
    resources = ", ".join(p.resources) if p.resources else "—"
    return (
        f"🏭 <b>{p.company_name}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🌐 Сфера: {p.sphere}\n"
        f"🔍 Ищем: {needs}\n"
        f"💼 Предлагаем: {resources}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📞 Контакт: {p.contact_person}"
    )
