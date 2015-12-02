from click import ClickException, echo
#from click.utils import ClickException

class FatalError(ClickException):
    """An exception to show to the user"""

    # The exit code for this exception
    exit_code = 1

    #def __init__(self, message):
    #    Exception.__init__(self, message)
    #    self.message = message

    #def format_message(self):
    #    return self.message

    def show(self):
        echo(self.message)


class InvalidOption(Exception):
    pass


class NoValidatorError(Exception):
    pass
