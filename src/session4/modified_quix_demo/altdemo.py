#!/usr/bin/env python3
r"""An alternative Quixote demo.  This version is contained in a single module
and does not use PTL.  The easiest way to run this demo is to use the
simple HTTP server included with Quixote.  For example:

    $ python -m quixote run --app modified_quix_demo.altdemo

or
    $ uv run python -m quixote run --app modified_quix_demo.altdemo

(you might need to do this from the tests directory).

The server listens on localhost:8080 by default.  Debug and error output
will be sent to the terminal.

"""

from __future__ import annotations

from tempfile import TemporaryDirectory
from typing import cast

from quixote import (
    current_session,
    current_session_manager,
    get_field,
    get_session,
    get_user,
)
from quixote.directory import Directory
from quixote.html import href, htmltext
from quixote.publish import Publisher
from quixote.util import dump_request

from session4.DirectorySessionStore import DirectorySessionStore
from session4.Session4Session import Session4, Session4SessionManager

SESSIONS_DIRECTORY = TemporaryDirectory(delete=True)


def format_page(title: str, content: object) -> htmltext:
    request = (htmltext('<div style="font-size: smaller;background:#eee"><h1>Request:</h1>%s</div>') % dump_request())
    return (
            htmltext(
                '<html><head><title>%(title)s</title>'
                '<style type="text/css">\n'
                'body { border: thick solid green; padding: 2em; }\n'
                'h1 { font-size: larger; }\n'
                'th { background: #aaa; text-align:left; font-size: smaller; }\n'
                'td { background: #ccc; font-size: smaller; }\n'
                '</style>'
                '</head><body>%(content)s%(request)s</body></html>'
            )
            % locals()
    )


def format_request() -> htmltext:
    return format_page('Request', dump_request())


def format_link_list(targets: list[str]) -> htmltext:
    return htmltext('<ul>%s</ul>') % htmltext('').join(
        [htmltext('<li>%s</li>') % href(target, target) for target in targets]
    )


class RootDirectory(Directory):
    _q_exports = ['', 'login', 'logout']

    def _q_index(self) -> htmltext:  # noqa
        content = htmltext('')
        if not get_user():
            content += htmltext('<p>%s</p>' % href('login', 'login'))
        else:
            content += htmltext('<p>Hello, %s.</p>') % get_user()
            content += htmltext('<p>%s</p>' % href('logout', 'logout'))
        sessions = sorted([(s.id, s) for s in current_session_manager()])
        if sessions:
            content += htmltext(
                '<table><tr>'
                '<th></th>'
                '<th>Session</th>'
                '<th>User</th>'
                '<th>Number of Requests</th>'
                '</tr>'
            )
            this_session = get_session()
            for index, (id, session) in enumerate(cast(list[tuple[str, DemoSession]], sessions)):  # noqa
                if session is this_session:
                    formatted_id = htmltext('<span style="font-weight:bold">%s</span>' % id)
                else:
                    formatted_id = id
                content += htmltext('<tr><td>%s</td><td>%s</td><td>%s</td><td>%d</td>'
                                    % (
                                        index,
                                        formatted_id,
                                        session.user or htmltext("<em>None</em>"),
                                        session.num_requests,
                                    )
                                    )
            content += htmltext('</table>')
        return format_page("Quixote Session Management Demo", content)

    def login(self) -> htmltext:  # noqa
        content = htmltext('')
        if get_field("name"):
            session = current_session()
            session.set_user(get_field("name"))  # This is the important part.
            content += (htmltext('<p>Welcome, %s!  Thank you for logging in.</p>') % get_user())
            content += href("..", "go back")
        else:
            content += htmltext(
                '<p>Please enter your name here:</p>\n'
                '<form method="POST" action="login">'
                '<input name="name" />'
                '<input type="submit" />'
                '</form>'
            )
        return format_page("Session4 Demo: Login", content)

    def logout(self) -> htmltext:  # noqa
        if get_user():
            content = htmltext('<p>Goodbye, %s.</p>') % get_user()
        else:
            content = htmltext('<p>That would be redundant.</p>')
        content += href("..", "start over")
        # This is the important part.
        current_session_manager().expire_session()
        return format_page("Session4 Demo: Logout", content)


class DemoSession(Session4):
    num_requests: int

    def __init__(self, id: str) -> None:  # noqa
        super().__init__(id)
        self.num_requests = 0

    def start_request(self) -> None:
        """
        This is called from the main object publishing loop whenever
        we start processing a new request.  Obviously, this is a good
        place to track the number of requests made.  (If we were
        interested in the number of *successful* requests made, then
        we could override finish_request(), which is called by
        the publisher at the end of each successful request.)

        Quixote's original test-code overrode has_info() and then assigned
        is_dirty to be has_info: however, Session4 will automatically detect
        changes (in this case to num_requests) and returns is_dirty() accordingly.
        """
        super().start_request()
        self.num_requests += 1


def create_publisher() -> Publisher:
    session_store = DirectorySessionStore(sessions_directory=SESSIONS_DIRECTORY.name)
    session_manager = Session4SessionManager(session_store=session_store, session_class=DemoSession)
    pub = Publisher(root_directory=RootDirectory(), session_manager=session_manager)
    return pub
