# Session4: Persistent Session Management for Quixote 4+

Authors, copyright, and license

Session4 is copyrighted and made available under open source licensing terms for which
see [LICENSE.txt](LICENSE.txt) for the details.
The [ACKS.txt](ACKS.txt) file lists the orignial authors (of Session2) and anyone who has
assisted in the development.
[RELEASE_NOTES.md](doc/RELEASE_NOTES.md) summarizes the changes in the current release.

The current author is Robert Ladyman, <it@file-away.co.uk>

Version

:   0.1.0 released August 2026 (in development)

Status

:   Only the file-storage mechanism [DirectorySessionStore](src/session4/DirectorySessionStore.py) is currently
working with Quixote 4+

## Source code

The source code is managed using Git. You can check out a copy using the
command:

```
git clone https://github.com/rojalator/session4.git
```

## Introduction

[Quixote](https://github.com/nascheme/quixote) is a Python Web application framework. It comes with an in-memory session
manager, which works but is incompatible with multi-process servers (SCGI, CGI, etc).
It also (by design) forgets the sessions when the Publisher quits.
[Session4](https://github.com/rojalator/session4) provides replacement
session manager, session and store classes to allow persistence for sessions using Quixote.[^1]

Session4 version 0.1.0 provides a fully functional[^2] persistent storage back-end for use with
Quixote 4 and above (also see [Road-map](#road-map) below, for future session4 version notes):-

[DirectorySessionStore](https://rojalator.github.io/session4/literate/session4/store/DirectorySessionStore.html)
([DirectorySessionStoreAPI](https://rojalator.github.io/session4/session4.store.DirectorySessionStore.html))

Store each pickled session in a file in the designated directory.
The filename for a session is the session ID. Uses `fcntl` file locking. :

        DirectorySessionStore(directory)

This package includes an extended version of Quixote's ``BaseSessionManager``
that adds the missing `__getitem__()` and `has_session()` functions. Basing
this upon BaseSessionManager should allow Session4 to track changes in
Quixote much more efficiently (Session 3 had drifted considerably).
There is also a Session4 class based upon Quixote's Session that
automatically detects changes to attributes (which will be saved) and
returns the status (changed or not) via `is_dirty()`.

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

[API documentation](https://rojalator.github.io/session4/moduleIndex.html) is available as
is [Literate Programming documentation](https://rojalator.github.io/session4/literate/)
--- either read it on-line or extract it from the tar.gz file.

## Using session4

As usual for Quixote, you need a *store*, a *manager* and then you need to tell Quixote's
*publisher* to use them both but in addition you'll need to tell the session store
where to store sessions (at least for a ``DirectorySessionStore``).
For example, assuming the directory path is in ``some_location/``,
then in your ``create_publisher()`` function, you might place the following code:

    from session4.DirectorySessionStore import DirectorySessionStore
    from session4.Session4Session import Session4, Session4SessionManager

    # locate or create the session store.
    store = DirectorySessionStore(sessions_directory=some_location, create=True)

    # create the session manager.
    session_manager = Session4SessionManager(session_store=store, session_class=Session4)

    # create the publisher.
    publisher = Publisher(..., session_manager=session_manager)

Each session store has different initialization requirements: see
the [API documentation](https://rojalator.github.io/session4/moduleIndex.html) or
the [literate programming documentation](https://rojalator.github.io/session4/literate/)
for more information.

## Features

All session4 stores have the following convenience methods:--

`setup()`
: initializes the store. For DirectorySessionStores this does nothing: it is suggested that a directory
be created prior to initialisation, so that, for example, a temporary directory can be created or a
location can be loaded from Quixote's config file.

`.delete_old_sessions(minutes)`:
:   deletes sessions that haven't been modified for N minutes. This is
meant for your application maintenance program; e.g., a daily cron
job.

`.is_multiprocess_safe` and `.is_thread_safe`
: All stores have `.is_multiprocess_safe` and `.is_thread_safe`
attributes. An application can check these flags and abort if configured
inappropriately. The flags are defined as follows:-

- ``DirectorySessionStore`` is multiprocess safe because it uses `fcntl`
  file locking. This limits its use to POSIX. See the fcntl caution
  below. It may be thread safe because it always locks-unlocks within
  the same method, but we don't know for sure so the attribute is
  false.

### Testing

Session4 comes with both an automatic test suite (via pytest) and an interactive Quxiote test application.
To run tests, consult the [README.md](tests/README.md) file in the ``tests/`` directory.

### `fcntl` Caution

On Mac OS X when using PTL, import `fcntl` *before* enabling PTL.
Otherwise the import hook may load the deprecated FCNTL.py instead due
to the Mac's case-insensitive filesystem, which will cause errors down
the road. This was supposedly fixed in Python 2.4, which doesn't have
FCNTL.py.

### Changes from Session3

See [CHANGES.txt](doc/CHANGES.txt) in the ``doc/`` directory

------------------------------------------------------------------------

[^1]: Session3 is based upon the previous Session2 code (designed for,
unsurprisingly, Quixote 2)

[^2]: Note that only
[DirectorySessionStore](https://rojalator.github.io/session3/literate/session3/store/DirectorySessionStore.html)
is working for version 3.4
