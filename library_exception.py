class LibraryException(Exception):
    def __init__(self, err_msg):
        """ Initializes a library exception with the given error message.

        err_msg: str
        """
        Exception.__init__(self, err_msg)
