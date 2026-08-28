# Session4: Persistent Session Management for Quixote 4+

Authors

:   R J Ladyman, (based upon session2 by C Titus Brown and Mike Orr and session3 by R J Ladyman)
References in the code are:--
CTB: C. Titus Brown
MO: Mike Orr
RJLRJL: Robert Ladyman


Email

:   <it@file-away.co.uk>

License

:   MIT (<http://www.opensource.org/licenses/mit-license.php>)

Version

:   0.1.0 released August 2026

Status

:   Only the file-storage mechanism (DirectorySessionStore) is working
with Quixote 4+

::: contents
Contents
:::

## Introduction

[Quixote](https://github.com/nascheme/quixote) is a Python Web
application framework. It comes with an in-memory session manager, which
works but is incompatible with multi-process servers (SCGI, CGI, etc).
It also (by design) forgets the sessions when the Publisher quits.
[Session4](https://github.com/rojalator/session3) provides a new
session manager class and a simple back-end storage API to allow
persistence for sessions.[^1]

Session4 version 0.1.0 provides a fully functional[^2] persistent
storage back-end for use with Quixote 4 and above (also see
[Road-map](#road-map) below, for later version notes):-

[DirectorySessionStore](https://rojalator.github.io/session3/literate/session3/store/DirectorySessionStore.html) ([DirectorySessionStoreAPI](https://rojalator.github.io/session3/session3.store.DirectorySessionStore.html))

:   Store each pickled session in a file in the designated directory.
The filename is the session ID. Uses `fcntl` file locking. :

        DirectorySessionStore(directory)

This package includes an extended version of Quixote's BaseSessionManager
that adds the missing `__getitem__()` and `has_session()` functions. Basing
this upon BaseSessionManager should allow Session4 to track changes in
Quixote much more efficiently (Session 3 had drifted considerably).
[SessionManager](https://rojalator.github.io/session3/literate/session3/SessionManager.html)
([SessionManagerAPI](https://rojalator.github.io/session3/session3.SessionManager.SessionManager.html))
It also has a Session4 class based upon Quixote's Session that
automatically detects changes to attributes (which will be saved) and returns the status via `is_dirty()`.

It's quite likely that the session stores can be adapted for use with
other Web frameworks; let us know if you do this so we can link to you
and / or include helpful code in the package.

### Road-map

* Session 4 will add support for Postgres, MySQL, Shelve and other back-ends
  as required.
* Ability to use Session 4 without Quixote (either as Session4 itself or, for
  example, via Session4NoQuixote)

## Getting Session4

### Installation

Session4 can be installed via pip (`pip3 install session4`).
Alternatively (or if you also want the documentation) download and
unpack the tar.gz file and install the normal Python way
(`python4 setup.py install`). Note that Session4 requires Quixote 4 or
greater which is also available via pip or from
[Quixote](https://github.com/nascheme/quixote)'s repository.

### Documentation

[API
documentation](https://rojalator.github.io/session3/moduleIndex.html) is
available as is [Literate Programming
documentation](https://rojalator.github.io/session3/literate/)
 --- either read it on-line or extract it from the tar.gz file.

## Using session3

You need a *store*, a *manager* and then you need to tell Quixote\'s
*publisher* to use them both: in your [create_publisher()]{.title-ref}
function, place the following code:

    # create the session store.
    from session3.store.DirectorySessionStore import DirectorySessionStore
    from session3.SessionManager import SessionManager

    # create the session manager.
    store = DirectorySessionStore(path.expanduser(some_location), create=True)
    session_manager = SessionManager(store)

    # create the publisher.
    from quixote.publish import Publisher
    publisher = Publisher(..., session_manager.session_manager)

Each session store has different initialization requirements:[^3] see
the [API
documentation](https://rojalator.github.io/session3/moduleIndex.html) or
the [literate programming
documentation](https://rojalator.github.io/session3/literate/) for more
information.

## Features

All session4 stores have the following methods, which are called by the
session manager:-

`.load_session`, `.save_session`, `.delete_session`, `.has_session`.

They also have these convenience methods:-

`.setup()`:

:   initializes the store.

`.delete_old_sessions(minutes)`:

:   deletes sessions that haven't been modified for N minutes. This is
meant for your application maintenance program; e.g., a daily cron
job.

`.iter_sessions()`:

:   Return an iterable of (id, session) for all sessions in the store.
This is for admin applications that want to browse the sessions. The
DirectorySession will raise a *NotImplementedError*[^4].

All stores have `.is_multiprocess_safe` and `.is_thread_safe`
attributes. An application can check these flags and abort if configured
inappropriately. The flags are defined as follows:-

- DirectorySessionStore is multiprocess safe because it uses `fcntl`
  file locking. This limits its use to POSIX. See the fcntl caution
  below. It may be thread safe because it always locks-unlocks within
  the same method, but we don't know for sure so the attribute is
  false.[^5]

### Interactive Testing

Session4 comes with an automatic and interactive Quxiote test
application. To run it, consult the README.md file in the **test/**
directory.

### `fcntl` Caution

On Mac OS X when using PTL, import `fcntl` *before* enabling PTL.
Otherwise the import hook may load the deprecated FCNTL.py instead due
to the Mac\'s case-insensitive filesystem, which will cause errors down
the road. This was supposedly fixed in Python 2.4, which doesn't have
FCNTL.py.

### Changes from Session2

Since Session2 was released a number of packages that were referred to
in the documentation (and the source) have either ceased to exist or
moved into maintenance mode and Session3 itself is solely for Python 3.

> - [Nose](https://nose.readthedocs.io/en/latest/) is in maintenance
    > mode
> - The original web-site for [Twill](https://pypi.org/project/twill/)
    > has disappeared. Existing Twill code appears to be Python 2 only.
    > There is a new version at
    > [TwillTools](https://github.com/twill-tools/twill)

------------------------------------------------------------------------

[^1]: Session3 is based upon the previous Session2 code (designed for,
unsurprisingly, Quixote 2)

[^2]: Note that only
[DirectorySessionStore](https://rojalator.github.io/session3/literate/session3/store/DirectorySessionStore.html)
is working for version 3.4

[^3]: Note that only
[DirectorySessionStore](https://rojalator.github.io/session3/literate/session3/store/DirectorySessionStore.html)
is working for version 3.4

[^4]: For the Session2 code, this *was* implemented but *only* for MySQL

[^5]: Note that only
[DirectorySessionStore](https://rojalator.github.io/session3/literate/session3/store/DirectorySessionStore.html)
is working for version 3.4
