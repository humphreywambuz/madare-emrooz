from enum import StrEnum


class BloodType(StrEnum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"

    @property
    def is_rh_negative(self) -> bool:
        return self.value.endswith("-")


class ReproductiveStatus(StrEnum):
    TRYING_TO_CONCEIVE = "trying_to_conceive"
    PREGNANT = "pregnant"
    POSTPARTUM = "postpartum"


class JoinGoal(StrEnum):
    PREGNANCY = "pregnancy"
    FITNESS = "fitness"
    REHABILITATION = "rehabilitation"


class HomePath(StrEnum):
    """Which home screen the app opens after sign-in."""

    PREGNANCY = "pregnancy"
    TRYING_TO_CONCEIVE = "trying_to_conceive"  # simple page until later phases
    POSTPARTUM = "postpartum"  # offers the fitness and postpartum rehabilitation paths
    FITNESS = "fitness"
    REHABILITATION = "rehabilitation"
