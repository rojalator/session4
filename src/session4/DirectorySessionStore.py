"""
Store sessions in individual files within a directory.

### Note
There was a problem with the existing code (adopted from
the Python 2 version), which lead to an "EOFError: Ran out of input" exception

The code in save_session() did:

    f = open(filename, 'wb')

...which immediately made the file zero bytes long. You can try this out in 2
terminals (where `s` is some dummy class with `s.id` as the file-name) with one doing:

    import pickle
    pickle.dump(s, f, 4)
    f.close()
    f = open(s.id, 'wb')

If in the other terminal you do:

    f = open(s.id, 'rb')
    o = pickle.load(f)
    Traceback (most recent call last):
    ...EOFError: Ran out of input

This is not entirely unexpected BUT the code in `load_session()`:

    f = open(filename, 'rb')
    fcntl.flock(f.fileno(), fcntl.LOCK_SH)

...could get the shared lock (LOCK_SH) after save_session() performed
the open() but BEFORE `save_session()` got a chance to get the exclusive lock:

    f = open(filename, 'wb')
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)

(You can try it in the older code by quickly refreshing a browser calling a Quixote server.)

What happened appears to have been:

  1. save_session() opens the file to write  [f = open(filename, 'wb')]
  2. load_session() opens the file to read   [f = open(filename, 'rb')]
  3. load_session() asks for and GETS a shared lock [fcntl.LOCK_SH]
  4. save_session() asks for an exclusive lock BUT gets blocked by the shared lock
  5. load_session() tries to load the object and gets zero bytes. It then closes the file, mistakenly allowing save_session() to proceed.

As save_session() truncated the file and then waited for an exclusive lock, we had to have
load_session() check for a zero-sized file. If it has one, then save_session() has just created (or re-created)
it and we should let go and try again.

The originial code worked fine on hard discs but begain failing when SSDs came into use (due to speed, I suspect)

### Addendum
It turns out that, during testing, one can get at `EOFError` from pickle anyway, so a check for that was added too.

"""
from collections.abc import Iterator
import fcntl
import os
import os.path
from pathlib import Path
import pickle
import time
from pickle import dump, load

from quixote.session import SessionStore
from session4.Session4Session import Session4 as Session


class DirectorySessionStore(SessionStore):
    """
    Store sessions in individual files within a directory.
    The noqa in the definitions are because 'id' is a Python keyword (blame Quixote, not me!)
    """

    is_multiprocess_safe = True  # Needs file locking; OS-specific, limited to POSIX
    is_thread_safe = False  # Needs file locking or synchronization.
    # For Python3 we now use the highest protocol
    pickle_protocol = pickle.HIGHEST_PROTOCOL
    SLEEPY_TIME = 0.1  # See notes on save_ and load_session

    def load_session(self, id: str | None) -> Session | None:  # noqa
        """Load the pickled session from a file if it exists, otherwise return None"""
        if not id:
            return None
        filename = self._make_filename(id)
        finished: bool = False
        pickled_obj = None
        while not finished:
            try:
                f = open(filename, 'rb')
                # Sometimes we get the following lock AFTER `save_session()` has created
                # the file but BEFORE it has locked it. If so, we'll have a zero-sized file
                # (hence the loop, BTW, so don't be tempted to remove it).
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                if os.stat(f.fileno()).st_size == 0:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    f.close()
                    # Wait around for a bit and then loop...
                    time.sleep(DirectorySessionStore.SLEEPY_TIME)
                else:
                    try:
                        pickled_obj = load(f)
                        # **Don't be tempted to move this into a finally**
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                        f.close()
                        finished = True
                    except EOFError:
                        # Sometimes we'll also get `EOFError` from pickle anyway, so we might
                        # as well trap for that too (and then loop)...
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                        f.close()
                        time.sleep(DirectorySessionStore.SLEEPY_TIME)

            except OSError:
                return None
        return pickled_obj

    def save_session(self, session: Session) -> None:
        """Pickle the session and save it into a file."""
        filename = self._make_filename(session.id)
        f = open(filename, 'wb')
        # We wait at the following statement until we get an exclusive lock.
        # Note that `load_session()` can sometimes jump in here before we get the lock
        # (the naughty thing) but it will get a zero-sized file (`wb` mode truncates the file)
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            session.preserve_current_values()
            dump(session, f, self.pickle_protocol)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            f.close()

    def delete_session(self, session_id: str | None) -> None:
        """
        Delete the session file.
        """
        if session_id:
            filename: str = self._make_filename(session_id)
            os.unlink(filename)

    def has_session(self, id: str | None) -> bool:  # noqa
        """Return true if the session exists in the store, else false."""
        return self.load_session(id) is not None

    def __iter__(self) -> Iterator[str]:
        """Return an iterator of all session IDs in the storage.
        In our case, the session id is just the file-name"""
        all_files = Path(self.directory).glob('*')
        the_ids = [p.name for p in all_files if p.is_file()]
        return iter(the_ids)

    def transaction_start(self) -> None:
        """Called near the beginning of each request: after the HTTPRequest
        object has been built, but before we traverse the URL or call the
        callable object found by URL traversal.
        """
        pass

    def transaction_commit(self, session: Session | None) -> None:
        """Called near the end of each successful request.  Not called if
        there were any errors processing the request.
        """
        pass

    def transaction_abort(self, session: Session | None) -> None:
        """Called near the end of a failed request (i.e. a exception that was
        not a PublisherError was raised.
        """
        pass

    def __init__(self, sessions_directory: str, create_directory: bool = False):
        """
        `__init__` takes a directory name, with an option to create it if
        it's not already there.
        """
        sessions_directory = os.path.abspath(sessions_directory)

        # Make sure the directory exists:
        if not os.path.exists(sessions_directory):
            if create_directory:
                os.mkdir(sessions_directory)
            else:
                raise OSError("error, '%s' does not exist." % (sessions_directory,))

        # Is it actually a directory?
        if not os.path.isdir(sessions_directory):
            raise OSError("error, '%s' is not a directory." % (sessions_directory,))

        self.directory = sessions_directory

    def _make_filename(self, id: str) -> str:  # noqa
        """Build the filename from the session ID."""
        return os.path.join(self.directory, id)

    def delete_old_sessions(self, minutes: int | float) -> tuple[int, int]:
        """
        Delete all sessions that have not been modified for N minutes.

        This method is never called by the session manager.  It's for
        your application maintenance program; e.g., a daily cron job.

        DirectorySessionStore.delete_old_sessions returns a tuple:

            (n_deleted, n_remaining)
        """
        sessions_deleted: int = 0
        sessions_remaining: int = 0
        for session_id in os.listdir(self.directory):
            path = self._make_filename(session_id)
            mtime = os.stat(path).st_mtime
            inactive_for = (time.time() - mtime) / 60.0

            if inactive_for > minutes:
                os.unlink(path)
                sessions_deleted += 1
            else:
                sessions_remaining += 1

        return sessions_deleted, sessions_remaining

    def setup(self):
        """
        Nothing to do here: but a directory could be created, etc.
        """
        pass
