from rfc3339 import rfc3339

import os
import shutil
import logging
from urllib.parse import urljoin

from django.core.management.base import BaseCommand
from django import urls

from core import models
from onisite import settings

log = logging.getLogger(__name__)

# Per https://www.sitemaps.org/protocol.html, max URLs is 50k per file
MAX_URLS = 50000

class Command(BaseCommand):
    help = '''
        Creates a sitemap.xml with links to other sitemap files as needed in
        order to provide search engines every relevant page in your Open ONI
        instance. The index will include links for all batches, titles, issues,
        and pages, as well as the OCR representations of the pages. It is
        expected that you will have custom urls in static/sitemaps/custom.xml
        for any other pages you deem relevant, including the homepage.

        Sitemaps are generated in a temporary location and don't move to their
        final location until the operation is complete in order to avoid broken
        sitemaps replacing working ones.
    '''

    def handle(self, **options):
        self.tmpdir = 'static/sitemap-tmp'
        self.proddir = 'static/sitemaps'

        shutil.rmtree(self.tmpdir, ignore_errors = True)
        os.makedirs(self.tmpdir, exist_ok = False)
        self.write_sitemaps()
        shutil.rmtree(self.proddir, ignore_errors = True)
        os.rename(self.tmpdir, self.proddir)

    def write_sitemaps(self):
        """
        Writes a sitemap index file that references individual sitemaps for all the
        batches, issues, pages and titles that have been loaded.
        """

        self.sitemap_id = 0
        self.urls = []
        self.indexes = []

        for loc, last_mod in sitemap_urls():
            self.urls.append((os.path.join(settings.BASE_URL, loc), last_mod))
            if len(self.urls) >= MAX_URLS:
                self.write_sitemap()

        self.write_sitemap()
        self.write_sitemap_index()

    def write_sitemap(self):
        if len(self.urls) == 0:
            return

        self.sitemap_id += 1
        name = 'sitemap-%05d.xml' % self.sitemap_id
        path = os.path.join(self.tmpdir, name)
        log.info('Writing sitemap "%s"' % path)

        with open(path, 'w') as file:
            file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            file.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            for url, last_mod in self.urls:
                file.write('\t<url>\n')
                file.write('\t\t<loc>%s</loc>\n' % urljoin(settings.BASE_URL, url))
                file.write('\t\t<lastmod>%s</lastmod>\n' % rfc3339(last_mod))
                file.write('\t</url>\n')
            file.write('</urlset>\n')

        self.indexes.append(urljoin(settings.BASE_URL, name))
        self.urls = []

    def write_sitemap_index(self):
        path = os.path.join(self.tmpdir, 'sitemap.xml')
        sitemap_index = open(path, 'w')
        sitemap_index.write('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        sitemap_index.write('<sitemap><loc>%s</loc></sitemap>\n' % urljoin(settings.BASE_URL, 'sitemap-custom.xml'))

        for sitemap in self.indexes:
            sitemap_index.write('<sitemap><loc>%s</loc></sitemap>\n' % sitemap)

        sitemap_index.write('</sitemapindex>\n')
        sitemap_index.close()

def sitemap_urls():
    """
    A generator that returns all the urls for batches, issues, pages and
    titles, and their respective modified time as a tuple.
    """
    for batch in models.Batch.objects.all():
        yield batch.url, batch.created
        for issue in batch.issues.all():
            yield issue.url, batch.created
            for page in issue.pages.all():
                # There's no shortcut for the non-XML OCR URL, so we have to
                # build it via urls.reverse
                ocr_html_url = urls.reverse('openoni_page_ocr', kwargs={
                    "lccn": issue.title.lccn,
                    "date": issue.date_issued,
                    "edition": issue.edition,
                    "sequence": page.sequence
                })

                yield page.url, batch.created
                yield ocr_html_url, batch.created
                yield page.ocr_url, batch.created
                yield page.txt_url, batch.created
                yield page.pdf_url, batch.created

    for title in models.Title.objects.all():
        yield title.url, title.created
