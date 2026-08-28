"""Tests for Session, form/CSRF tokens, and SessionManager: adopted from Quixote 4

Constructing a Session reads the current request (remote address), so
these tests run inside a publisher request context.  The cookie
lifecycle tests use a publisher configured with a real BaseSessionManager (well
a Session4SessionManager) instead of the default NullSessionManager.
"""

from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

# do this with logging so that we can get print() output and the use
# --log-cli-level=DEBUG with pytest
# import logging
# logging.basicConfig(level=logging.DEBUG)  # noqa

import pytest
from helpers import request_context

import quixote
from quixote.directory import Directory
from quixote.publish import Publisher
from quixote.session import CSRF_TOKEN_NAME

# We import our own session as it handles detecting changes
from session4.Session4Session import Session4, Session4SessionManager
from session4.DirectorySessionStore import DirectorySessionStore


class Root(Directory):
    _q_exports = ['']

    def _q_index(self) -> str:  # noqa
        return 'index'


base_session_path: str | None = None


@pytest.fixture
def session_publisher() -> Iterator[Publisher]:
    """A publisher whose sessions are kept by a real SessionManager."""
    # We need a temporary directory for the DirectorySessionStore to play with: cleans itself up at the end
    global base_session_path
    with TemporaryDirectory(delete=True) as sessions_directory:
        # We need a particular session store: currently just a DirectorySessionStore
        base_session_path = sessions_directory
        session_store = DirectorySessionStore(sessions_directory=sessions_directory)
        session_manager = Session4SessionManager(session_store=session_store, session_class=Session4)
        pub = Publisher(Root(), session_manager=session_manager)
        try:
            yield pub
        finally:
            quixote.cleanup()


def file_exists(file_path: str) -> bool:
    return Path(base_session_path + '/' + file_path).exists()


class TestSession:
    def test_a_new_session_is_empty(self, session_publisher: Publisher) -> None:
        with request_context(session_publisher):
            session = Session4('abc')
        assert session.id == 'abc'
        assert session.get_user() is None
        assert session.get_remote_address() == '127.0.0.1'
        assert session.has_info() is False

    def test_setting_a_user_gives_the_session_info(self, session_publisher: Publisher) -> None:
        with request_context(session_publisher):
            session = Session4(None)
        session.set_user('alice')
        assert session.get_user() == 'alice'
        assert session.has_info() is True
        assert session.is_dirty() is True

    def test_start_request_exports_the_user_to_the_environ(self, session_publisher: Publisher) -> None:
        with request_context(session_publisher) as request:
            session = Session4(None)
            session.set_user('alice')
            session.start_request()
            assert request.get_environ('REMOTE_USER') == 'alice'
            assert session.is_dirty() is True


class TestFormTokens:
    def test_created_tokens_are_outstanding_until_removed(self, session_publisher: Publisher) -> None:
        with request_context(session_publisher):
            session = Session4(None)
        token = session.create_form_token()
        assert session.has_form_token(token) is True
        assert session.is_dirty() is True
        session.remove_form_token(token)
        assert session.has_form_token(token) is False

    def test_the_oldest_token_is_dropped_beyond_the_maximum(self, session_publisher: Publisher) -> None:
        with request_context(session_publisher):
            session = Session4(None)
        first = session.create_form_token()
        last = first
        for _i in range(Session4.MAX_FORM_TOKENS):
            last = session.create_form_token()
        assert session.has_form_token(first) is False
        assert session.has_form_token(last) is True


class TestCsrfTokens:
    def test_the_csrf_token_is_stable_within_a_session(self, session_publisher: Publisher) -> None:
        with request_context(session_publisher):
            session = Session4(None)
        assert session.get_csrf_token() == session.get_csrf_token()
        assert session.is_dirty() is True

    def test_a_get_request_never_validates(self, session_publisher: Publisher) -> None:
        with request_context(session_publisher) as request:
            session = Session4(None)
            request.form[CSRF_TOKEN_NAME] = session.get_csrf_token()
            assert session.valid_csrf_token() is False

    def test_a_post_with_the_matching_token_validates(self, session_publisher: Publisher) -> None:
        with request_context(session_publisher, method='POST') as request:
            session = Session4(None)
            request.form[CSRF_TOKEN_NAME] = session.get_csrf_token()
            assert session.valid_csrf_token() is True

    def test_a_post_with_a_wrong_token_does_not_validate(self, session_publisher: Publisher) -> None:
        with request_context(session_publisher, method='POST') as request:
            session = Session4(None)
            session.get_csrf_token()
            request.form[CSRF_TOKEN_NAME] = 'wrong'
            assert session.valid_csrf_token() is False


class TestSessionLifecycle:
    def test_start_request_attaches_a_session_to_the_request(self, session_publisher: Publisher) -> None:
        manager = session_publisher.session_manager
        with request_context(session_publisher) as request:
            manager.start_request()
            assert isinstance(request.session, Session4)
            assert request.session.id is None

    def test_a_session_with_info_is_stored_and_sets_the_cookie(self, session_publisher: Publisher) -> None:
        manager = session_publisher.session_manager
        with request_context(session_publisher) as request:
            session = Session4(None)
            session.set_user('alice')
            manager.maintain_session(session)
            assert session.is_dirty() is False
            assert file_exists(session.id)
            assert session.id is not None
            assert session.id in manager
            cookie = request.response.cookies['QX_session']
            assert cookie['value'] == session.id
            session.set_user('Not alice')
            assert session.is_dirty() is True

    def test_a_session_that_lost_its_info_is_forgotten(self, session_publisher: Publisher) -> None:
        manager = session_publisher.session_manager
        with request_context(session_publisher) as request:
            session = Session4(None)
            session.set_user('alice')
            manager.maintain_session(session)
            assert file_exists(session.id)
            session.set_user(None)
            manager.maintain_session(session)
            assert not file_exists(session.id)
            assert session.id not in manager
            cookie = request.response.cookies['QX_session']
            assert cookie['value'] == ''
            assert cookie['max_age'] == 0

    def test_expire_session_forgets_the_current_session(self, session_publisher: Publisher) -> None:
        manager = session_publisher.session_manager
        with request_context(session_publisher) as request:
            session = Session4(None)
            session.set_user('alice')
            assert session.is_dirty() is True
            manager.maintain_session(session)
            assert session.is_dirty() is False
            assert file_exists(session.id)
            request.session = session
            manager.expire_session()
            assert session.id not in manager
            assert request.session is None
            assert not file_exists(session.id)


class TestSessionManagerRetention:
    def test_stored_sessions_are_found_again(self, session_publisher: Publisher) -> None:
        manager = session_publisher.session_manager
        with request_context(session_publisher):
            session = manager.new_session('sid1')
            assert session.is_dirty() is True
            manager.store.save_session(session)
            assert session.is_dirty() is False
            # Check is_dirty doesn't change anything
            assert session.is_dirty() is False
        assert manager.__contains__('sid1') is True
        assert 'sid1' in manager
        assert file_exists(session.id)
        assert session.is_dirty() is False
        assert session.is_dirty() is False
        # Can we load it?
        saved_session = manager.get(session.id)
        assert session.is_dirty() is False
        assert saved_session.id == session.id
        assert file_exists(saved_session.id)
        # it should be unchanged
        assert saved_session.is_dirty() is False
        assert session.is_dirty() is False

    def test_missing_sessions_give_the_default_or_raise(self, session_publisher: Publisher) -> None:
        manager = session_publisher.session_manager
        assert manager.get('nope', 'dflt') == 'dflt'
        assert 'nope' not in manager
        assert not file_exists('nope')
        # Now delete the non-existent session
        with pytest.raises(FileNotFoundError):
            manager.store.delete_session('nope')

    def test_deleted_sessions_are_gone(self, session_publisher: Publisher) -> None:
        manager = session_publisher.session_manager
        with request_context(session_publisher):
            session = manager.new_session('sid2')
            manager.store.save_session(session)
            assert session.is_dirty() is False
        assert manager.__contains__('sid2') is True
        assert file_exists(session.id)
        # Now get rid of it...
        del manager['sid2']
        # It should be gone...
        assert manager.get('sid2', default='none_such') == 'none_such'
        assert manager.__contains__('sid2') is False
        assert 'sid2' not in manager
        assert not file_exists(session.id)

    def test_delete_all_sessions_wait_60(self, session_publisher: Publisher) -> None:
        manager = session_publisher.session_manager
        with request_context(session_publisher):
            # Create a bunch of sessions...
            for i in range(0, 5):
                session = manager.new_session(str(i))
                manager.store.save_session(session)
                assert file_exists(str(i))
            # We need to wait for 60+ seconds but we'll cheat with a (-)ve number
            deleted, remaining = manager.store.delete_old_sessions(-1)  # noqa
            for i in range(0, 5):
                assert manager.__contains__(str(i)) is False
                assert str(i) not in manager
                assert not file_exists(str(i))
            assert deleted == 5
            assert remaining == 0
            # Create a new one which should not get deleted
            session = manager.new_session('not_old_session')
            manager.store.save_session(session)
            assert 'not_old_session' in manager
            deleted, remaining = manager.store.delete_old_sessions(1)  # noqa
            assert not deleted and remaining == 1


class TestSessionValues:
    def test_forced_save_and_load_of_additional_data(self, session_publisher: Publisher) -> None:
        manager = session_publisher.session_manager
        with request_context(session_publisher):
            session = manager.new_session(None)
            session.set_user("I'm Dirty")
            assert session.is_dirty() is True

            manager.maintain_session(session)
            assert session.is_dirty() is False
            assert file_exists(session.id)

            session.additional_value = 'some value'
            assert session.is_dirty() is True
            manager.maintain_session(session)
            assert session.is_dirty() is False

            # Now fetch from disk and check we have the new value
            session2 = manager.get(session.id)
            assert session2.additional_value == 'some value'
            assert session2.is_dirty() is False

    def test_is_dirty(self, session_publisher: Publisher) -> None:
        # Check that adding or changing a value results in a save
        # Lists and their cousins are problematic
        manager = session_publisher.session_manager
        with request_context(session_publisher):
            session = manager.new_session('dirty_test')
            session.set_user('Fred')
            session.some_list = ['a', 'list']
            assert session.is_dirty() is True
            manager.store.save_session(session)
            assert session.is_dirty() is False
            # Re-assign with same contents
            session.some_list = ['a', 'list']
            assert session.is_dirty() is False
            session = manager.get('dirty_test')
            assert session.is_dirty() is False
            # Mutate a list
            session.some_list.append('added')
            assert session.is_dirty() is True
            manager.maintain_session(session)
            session = manager.get('dirty_test')
            assert session.some_list == ['a', 'list', 'added']


class TestManagerSetGet:
    def test_stored_sessions_are_found_again_setget(self, session_publisher: Publisher) -> None:
        manager = session_publisher.session_manager
        with request_context(session_publisher):
            session = Session4('sid1')
        manager['sid1'] = session
        assert 'sid1' in manager
        assert manager.has_session('sid1') is True  # noqa
        assert manager.__contains__('sid1') is True
        assert manager['sid1'].id == session.id  # noqa

    def test_nonsuch_id_raises_error_setget(self, session_publisher: Publisher):
        manager = session_publisher.session_manager
        with pytest.raises(KeyError):
            _ = manager['no such key']  # noqa

    def test_missing_sessions_give_the_default_or_raise_setget(self, session_publisher: Publisher) -> None:
        manager = session_publisher.session_manager
        assert manager.get('nope', 'dflt') == 'dflt'
        assert 'nope' not in manager
        with pytest.raises(FileNotFoundError):
            del manager['nope']
