# Open ONI Sitemap Plugin

This provides a new command to build a full sitemap for an Open ONI site.
Currently there is no configuration, and this is more a proof of concept than
anything else.

## Compatibility

The "main" branch should not be considered stable.  Unlike the core Open ONI
repository, plugins don't warrant the extra overhead of having separate
development branches, release branches, etc.  Instead, it is best to find a tag
that works and stick with that tag.

## Setup

Download the repository into the Open ONI's `onisite/plugins` directory as `sitemap`:

```
git clone git@github.com:jechols/oni-sitemap-plugin.git sitemap
```

`onisite.plugins.sitemap` needs to go in your `INSTALLED_APPS` list, e.g.:

```python
# onisite/settings_local.py

INSTALLED_APPS = (
    'django.contrib.humanize',
    'django.contrib.staticfiles',

    'onisite.plugins.sitemap',
    'themes.default',
    'core',
)
```

You **must create** a custom sitemap file in your ONI static files directory
(typically `static/sitemap-custom.xml`). At a minimum, you likely want your
homepage, but any URLs that aren't covered by this tool, which you want crawled
by search engines, can be added. This project contains an example you can base
your custom sitemap on.

## Usage

This just adds a new `build_sitemap` management command. Execute that as you
would any other management command, and your sitemaps will be created, e.g.:

```bash
cd /opt/openoni
./manage.py build_sitemap
```

You probably want to run this in a cron job, and likely not too often, as it
can take a long time to produce a list of every important URL on your site.

### Apache Setup

You will want your web server to serve up sitemap files, as ONI currently
doesn't do this (partly to avoid search engine hits that have to go through the
whole Django stack).

For Apache, Open ONI has a mostly-working example of how to set this up, but
the two directives you'll have to include are below:

```apache
AliasMatch ^/sitemap.xml$ /opt/openoni/static/sitemaps/sitemap.xml
AliasMatch ^/(sitemap-\w+.xml)$ /opt/openoni/static/sitemaps/$1
```

Note that, as of the time of creating this plugin, ONI's example assumes you'll
only have `sitemap.xml` and `sitemap-<number>.xml`. With the addition of a
custom sitemap, the second rule above would replace the digits-only match in
the ONI example.
