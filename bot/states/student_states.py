from vkbottle.dispatch.dispenser.base import BaseStateGroup


class StudentForm(BaseStateGroup):
    NAME = "student_name"
    SURNAME = "student_surname"
    UNIVERSITY = "student_university"
    YEAR = "student_year"
    FACULTY = "student_faculty"
    DIRECTIONS = "student_directions"
    TECH_INTERESTS = "student_tech_interests"
    SKILLS = "student_skills"
    PORTFOLIO = "student_portfolio"
    DESCRIPTION = "student_description"
    GOAL = "student_goal"
