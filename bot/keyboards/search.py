from vkbottle import Callback, Keyboard, KeyboardButtonColor, Text

from bot.keyboards.registration import DIRECTIONS, STARTUP_STAGES


def search_filter_kb(entity: str) -> str:
    kb = Keyboard(one_time=True)

    if entity in ("startups", "students"):
        for i, d in enumerate(DIRECTIONS):
            kb.add(Text(d), color=KeyboardButtonColor.PRIMARY)
            if (i + 1) % 2 == 0:
                kb.row()

    if entity == "startups":
        kb.row()
        for stage in STARTUP_STAGES:
            kb.add(Text(f"Стадия: {stage}"), color=KeyboardButtonColor.SECONDARY)
            kb.row()

    kb.add(Text("🔍 Все"), color=KeyboardButtonColor.POSITIVE)
    kb.add(Text("🏠 Главное меню"), color=KeyboardButtonColor.SECONDARY)
    return kb.get_json()


def card_nav_kb(entity: str, page: int, total: int, entity_id: int, req_type: str, already_sent: bool) -> str:
    """Inline-клавиатура под карточкой (Callback-кнопки)."""
    kb = Keyboard(inline=True)

    # Навигация
    nav = []
    if page > 0:
        nav.append(Callback("◀️", {"a": "prev", "e": entity, "p": page - 1}))
    nav.append(Callback(f"{page + 1}/{total}", {"a": "noop"}))
    if page < total - 1:
        nav.append(Callback("▶️", {"a": "next", "e": entity, "p": page + 1}))

    for btn in nav:
        kb.add(btn, color=KeyboardButtonColor.SECONDARY)

    kb.row()
    if already_sent:
        kb.add(Callback("⏳ Заявка отправлена", {"a": "noop"}), color=KeyboardButtonColor.SECONDARY)
    else:
        kb.add(
            Callback("📩 Подать заявку", {"a": "apply", "rt": req_type, "id": entity_id}),
            color=KeyboardButtonColor.POSITIVE,
        )

    kb.row()
    kb.add(Callback("🚩 Пожаловаться", {"a": "report", "id": entity_id}), color=KeyboardButtonColor.NEGATIVE)
    return kb.get_json()


def incoming_request_kb(request_id: int) -> str:
    kb = Keyboard(inline=True)
    kb.add(Callback("✅ Принять", {"a": "req_accept", "id": request_id}), color=KeyboardButtonColor.POSITIVE)
    kb.add(Callback("❌ Отклонить", {"a": "req_reject", "id": request_id}), color=KeyboardButtonColor.NEGATIVE)
    return kb.get_json()
