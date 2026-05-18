from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud.partners import create_partner, get_partner_by_user_id, update_partner
from bot.database.crud.users import get_user_by_tg_id
from bot.keyboards.main_menu import back_to_menu_kb, confirm_kb
from bot.states.partner_states import PartnerForm
from bot.utils.formatters import fmt_partner
from bot.utils.validators import parse_comma_list, validate_text_length

router = Router()


async def start_registration(message: Message, state: FSMContext) -> None:
    await state.set_state(PartnerForm.company_name)
    await state.update_data(needs=[], resources=[])
    await message.answer(
        "📝 <b>Регистрация индустриального партнёра</b>\n\nВведите <b>название компании</b>:",
        parse_mode="HTML",
    )


@router.message(PartnerForm.company_name)
async def partner_company(message: Message, state: FSMContext) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Название должно быть от 2 до 128 символов:")
        return
    await state.update_data(company_name=message.text.strip())
    await state.set_state(PartnerForm.sphere)
    await message.answer("Введите <b>сферу деятельности</b>:", parse_mode="HTML")


@router.message(PartnerForm.sphere)
async def partner_sphere(message: Message, state: FSMContext) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Введите корректную сферу деятельности:")
        return
    await state.update_data(sphere=message.text.strip())
    await state.set_state(PartnerForm.needs)
    await message.answer(
        "Что вы ищете? Введите через запятую:\n"
        "<i>Пример: Стажёры, Стартапы для пилота, R&D проекты</i>",
        parse_mode="HTML",
    )


@router.message(PartnerForm.needs)
async def partner_needs(message: Message, state: FSMContext) -> None:
    needs = parse_comma_list(message.text)
    if not needs:
        await message.answer("Введите хотя бы один пункт:")
        return
    await state.update_data(needs=needs)
    await state.set_state(PartnerForm.resources)
    await message.answer(
        "Что вы предлагаете? Введите через запятую:\n"
        "<i>Пример: Инфраструктура, Мини-грант, Экспертиза</i>",
        parse_mode="HTML",
    )


@router.message(PartnerForm.resources)
async def partner_resources(message: Message, state: FSMContext) -> None:
    resources = parse_comma_list(message.text)
    if not resources:
        await message.answer("Введите хотя бы один пункт:")
        return
    await state.update_data(resources=resources)
    await state.set_state(PartnerForm.contact_person)
    await message.answer(
        "Введите имя и контакт <b>контактного лица</b>:\n"
        "<i>Пример: Иван Иванов, @iivanov</i>",
        parse_mode="HTML",
    )


@router.message(PartnerForm.contact_person)
async def partner_contact(message: Message, state: FSMContext) -> None:
    if not validate_text_length(message.text, 2, 128):
        await message.answer("Введите корректный контакт:")
        return
    await state.update_data(contact_person=message.text.strip())
    await state.set_state(PartnerForm.confirm)

    data = await state.get_data()
    from bot.database.models import Partner

    preview = Partner(
        user_id=0,
        company_name=data["company_name"],
        sphere=data["sphere"],
        needs=data.get("needs", []),
        resources=data.get("resources", []),
        contact_person=data["contact_person"],
    )

    await message.answer(
        f"<b>Проверьте вашу анкету:</b>\n\n{fmt_partner(preview)}\n\nВсё верно?",
        reply_markup=confirm_kb("partner:save", "menu:main"),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "partner:save")
async def partner_save(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    user = await get_user_by_tg_id(session, callback.from_user.id)
    existing = await get_partner_by_user_id(session, user.id)

    if existing:
        await update_partner(session, user.id, data)
    else:
        await create_partner(session, user.id, data)

    from bot.keyboards.main_menu import main_menu_kb
    from bot.database.models import UserRole

    await callback.message.edit_text(
        "✅ <b>Анкета партнёра сохранена!</b>",
        reply_markup=main_menu_kb(UserRole.partner),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:profile")
async def show_partner_profile(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await get_user_by_tg_id(session, callback.from_user.id)
    from bot.database.models import UserRole
    if user.role != UserRole.partner:
        return
    profile = await get_partner_by_user_id(session, user.id)
    if not profile:
        await callback.message.edit_text(
            "Анкета не найдена.", reply_markup=back_to_menu_kb()
        )
    else:
        await callback.message.edit_text(
            fmt_partner(profile), reply_markup=back_to_menu_kb(), parse_mode="HTML"
        )
    await callback.answer()
