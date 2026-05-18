from vkbottle.dispatch.dispenser.base import BaseStateGroup


class StartupForm(BaseStateGroup):
    NAME = "startup_name"
    DESCRIPTION = "startup_description"
    TAGS = "startup_tags"
    STAGE = "startup_stage"
    NEEDS = "startup_needs"
    CONTACT = "startup_contact"
