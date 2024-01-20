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
