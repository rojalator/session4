"""
This extends Quixote's session class to have auto-detection of added or changed
members or values, including lists, etc.

"""

from quixote.session import Session, BaseSessionManager


class Session4SessionManager(BaseSessionManager):
    """
    We sub-class the base version because that is missing __getitem__() and has_session()
    unfortunately. In future these might be added to Quixote's BaseSessionManager.
    See https://github.com/nascheme/quixote/issues/8
    """

    def __getitem__(self, item):
        if session := self.get(item, None):
            return session
        raise KeyError

    def has_session(self, key):
        return self.__contains__(key)


class Session4(Session):
    """
    This adapts Quixote's own Session class to overwrite is_dirty() so that

    Additional Instance attributes:
      _last_values : string
        the values of the session's attributes when it was last saved. is_dirty() uses
        this to compare with the current attributes (in memory) rendered as a string in order
        to automatically detect any added or changed attributes, including entries in things
        like lists and dictionaries (f'{vars(self)}' puts all the values into a string, which
        is handy to say the least). For fairly obvious reasons We remove _access_time and
        _last_values itself from the string to be stored.
    """
    # Bump up the form tokens as we've run out of them before
    MAX_FORM_TOKENS = 32
    # We preserve the last saved values as a string (lists wont save their contents otherwise)
    _last_values = ''

    def __init__(self, id: str | None) -> None:  # noqa
        super().__init__(id=id)
        self._last_values: str = ''

    def preserve_current_values(self):
        # Assign the current values, minus various things, to _last_values
        # Use a copy() or we'll manipulate the real __dict__ (oops!)
        current_vars = vars(self).copy()
        # Get rid of the _access_time as it will never match and then keep a copy of whatever the last values were
        current_vars.pop('_access_time', None)
        current_vars.pop('_last_values', '')
        # Now store it
        self._last_values = f'{current_vars}'

    def is_dirty(self) -> bool:
        # We cannot compare _access_time and aslo need to find (but exclude) '_last_values'
        # We'll have a copy of the last values when we were last loaded
        last_saved_values = self._last_values
        # What are our current values?
        current_vars = vars(self).copy()
        # Trim out what we do not need
        current_vars.pop('_access_time')
        current_vars.pop('_last_values')
        # Turn into a string for comparison
        current_values = f'{current_vars}'

        return current_values != last_saved_values
