import logging

logger = logging.getLogger(__name__)


class CustomException(Exception):
    def __init__(self, someattr: str):
        super().__init__(
            f"Custom specific message for attr: {someattr}"
        )


def tryme():
    attr = "*ATTR*"
    raise CustomException(attr)


if __name__ == "__main__":
    try:
        tryme()
    except Exception as e:
        logger.exception("Something bad happend")


### Output:
# ❯ python3 testme.py
# Something bad happend <<-- My log message
# Traceback (most recent call last):
#   File "/path/guilatrova/latrovacommits-articles/testme.py", line 19, in <module>
#     tryme()
#   File "/path/guilatrova/latrovacommits-articles/testme.py", line 14, in tryme
#     raise CustomException("*ATTR*")
# CustomException: Custom specific message for attr: *ATTR* <<-- My exception message
