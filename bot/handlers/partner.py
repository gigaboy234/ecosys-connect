from vkbottle.bot import BotLabeler, Message
from vkbottle.dispatch.rules.base import StateRule

from bot.database.crud.partners import create_partner, get_partner_by_user_id, update_partner
from bot.database.crud.users import get_user_by_tg_id
from bot.database.db import AsyncSessionLocal
from bot.database.models import Partner, UserRole
from bot.keyboards.main_menu import back_kb, confirm_kb, main_menu_kb
from bot.states.partner_states import PartnerForm
from bot.utils.formatters import fmt_partner
from bot.utils.validators import parse_comma_list, validate_text_length

labeler = BotLabeler()


async def start_registration(message: Message) -> None:
    await message.state_peer.set(PartnerForm.COMPANY_NAME)
    await message.state_peer.set_data({"needs": [], "resources": []})
    await message.answer("📝 Регистрация индустриального партнёра\n\nВведите название компании:")


@labeler.message(StateRule(PartnerForm.COMPANY_NAME))
async def partner_company(message: Message) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Название от 2 до 128 символов:")
        return
    d = await message.state_peer.get_data() or {}
    d["company_name"] = message.text.strip()
    await message.state_peer.set_data(d)
    await message.state_peer.set(PartnerForm.SPHERE)
    await message.answer("Введите сферу деятельности:")


@labeler.message(StateRule(PartnerForm.SPHERE))
async def partner_sphere(message: Message) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Введите корректную сферу:")
        return
    d = await message.state_peer.get_data() or {}
    d["sphere"] = message.text.strip()
    await message.state_peer.set_data(d)
    await message.state_peer.set(PartnerForm.NEEDS)
    await message.answer("Что вы ищете? Введите через запятую:\n(Пример: Стажёры, Стартапы для пилота)")


@labeler.message(StateRule(PartnerForm.NEEDS))
async def partner_needs(message: Message) -> None:
    needs = parse_comma_list(message.text)
    if not needs:
        await message.answer("Введите хотя бы один пункт:")
        return
    d = await message.state_peer.get_data() or {}
    d["needs"] = needs
    await message.state_peer.set_data(d)
    await message.state_peer.set(PartnerForm.RESOURCES)
    await message.answer("Что вы предлагаете? Введите через запятую:\n(Пример: Инфраструктура, Мини-грант)")


@labeler.message(StateRule(PartnerForm.RESOURCES))
async def partner_resources(message: Message) -> None:
    resources = parse_comma_list(message.text)
    if not resources:
        await message.answer("Введите хотя бы один пункт:")
        return
    d = await message.state_peer.get_data() or {}
    d["resources"] = resources
    await message.state_peer.set_data(d)
    await message.state_peer.set(PartnerForm.CONTACT_PERSON)
    await message.answer("Введите контактное лицо:\n(Пример: Иван Иванов, @iivanov)")


@labeler.message(StateRule(PartnerForm.CONTACT_PERSON))
async def partner_contact(message: Message) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Введите корректный контакт:")
        return
    d = await message.state_peer.get_data() or {}
    d["contact_person"] = message.text.strip()
    await message.state_peer.set_data(d)

    preview = Partner(
        user_id=0, company_name=d["company_name"], sphere=d["sphere"],
        needs=d.get("needs", []), resources=d.get("resources", []),
        contact_person=d["contact_person"],
    )
    await message.answer(
        f"Проверьте анкету:\n\n{fmt_partner(preview)}\n\nВсё верно?",
        keyboard=confirm_kb(),
    )


async def save_partner(message: Message) -> None:
    d = await message.state_peer.get_data() or {}
    await message.state_peer.delete()

    async with AsyncSessionLocal() as session:
        user = await get_user_by_tg_id(session, message.from_id)
        existing = await get_partner_by_user_id(session, user.id)
        if existing:
            await update_partner(session, user.id, d)
        else:
            await create_partner(session, user.id, d)

    await message.answer("✅ Анкета партнёра сохранена!", keyboard=main_menu_kb(UserRole.partner))


@labeler.message(text="🏭 Мой профиль")
async def show_partner_profile(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await get_user_by_tg_id(session, message.from_id)
        if not user or user.role != UserRole.partner:
            return
        profile = await get_partner_by_user_id(session, user.id)
        if not profile:
            await message.answer("Анкета не найдена.", keyboard=back_kb())
        else:
            await message.answer(fmt_partner(profile), keyboard=main_menu_kb(UserRole.partner))
