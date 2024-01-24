from .validation_error import ValidationError


def _chkGE(name: str, val: object, const: object):
    if val < const:
        raise ValidationError(
            f"Parameter {name} must be greater than or equal to {const}"
        )


def _chkGT(name: str, val: object, const: object):
    if val <= const:
        raise ValidationError(f"Parameter {name} must be greater than {const}")


def _chkTY(name: str, v1: object, v2: object):
    if type(v1) != v2:
        raise ValidationError(f"Parameter {name} must be of type {v1}")


def _chkV2(name: str, v1: object):
    if type(v1) != list and type(v1) != tuple:
        raise ValidationError(f"Parameter {name} must be of type list or tuple")
    if len(v1) != 2:
        raise ValidationError(f"Parameter {name} list/tuple must have length of 2.")


def _chkV3(name: str, v1: object):
    if type(v1) != list and type(v1) != tuple:
        raise ValidationError(f"Parameter {name} must be of type list or tuple")
    if len(v1) != 3:
        raise ValidationError(f"Parameter {name} list/tuple must have length of 3.")
