# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

import os
import iso8601
from sphinx import errors

# Gets the datestamp of the latest commit on the given file
# Converts the datestamp into something more readable
# Skips files whose datestamp we can't parse.

# Note: Outputs time in the commiters timezone.

# Example:
#   A commit with an iso8601 timestamp of 2020-01-05T15:27:40-05:00
#   will have a default output of "Jan 05, 2020 at 03:27 PM (UTC-0500)"


def page_context_handler(app, pagename, templatename, context, doctree):
    import git
    global g
    if g is None:
        # We have already errored about this
        pass
    fullpagename = pagename
    docsrc = ''
    try:
        docsrc = app.confdir + "/"
        if docsrc != "/":
            fullpagename = docsrc + pagename
    except KeyError:
        pass

    # Don't barf on "genindex", "search", etc
    if not os.path.isfile("%s.rst" % fullpagename):
        return

    try:
        updated = g.log('--pretty=format:%aI', '-n 1', "%s.rst" % fullpagename)

        if updated == "":
            # Don't datestamp generated rst's (e.g. imapd.conf.rst)
            # Ideally want to check their source - lib/imapoptions, etc, but
            # that involves getting the source/output pair into the extension.
            return

        tstamp = iso8601.parse_date(updated)

        context['gittstamp'] = tstamp.strftime(app.config.gitstamp_fmt)

    except git.exc.GitCommandError:
        # File doesn't exist or something else went wrong.
        raise errors.ExtensionError("Can't fetch git history for %s.rst." %
                                    fullpagename)
    except ValueError:
        # Datestamp can't be parsed.
        app.info("%s: Can't parse datestamp () %s ) for gitstamp, output \
            won't have last updated time." % (pagename, updated))
        pass


# Only add the page context handler if we're generating html
def what_build_am_i(app):
    global g
    if (app.builder.format != 'html'):
        return

    try:
        import git
    except ImportError:
        raise errors.ExtensionError("gitpython package not installed. \
            Required to generate html. Please run: pip install gitpython")

    try:
        global g
        g = git.Git('.')
    except:
        app.info(sys.exc_info()[0])
        app.warn("gitstamp extension enabled, but no git repository found. No \
            git datestamps will be generated.")
    else:
        app.connect('html-page-context', page_context_handler)


# We can't immediately add a page context handler: we need to wait until we
# know what the build output format is.
def setup(app):
    app.add_config_value('gitstamp_fmt', "%b %d, %Y at %I:%M %p (UTC%z)", 'html')
    app.connect('builder-inited', what_build_am_i)

    return {
        'parallel_read_safe': False
    }
