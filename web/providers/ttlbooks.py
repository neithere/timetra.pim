# -*- coding: utf-8 -*-
import os
from rdflib import Graph, Namespace, RDF, RDFS, URIRef

from .base import BaseDataProvider
from models import Document

from settings import get_app_conf


DATA_FILE = 'assets/books.ttl'
DATA_FORMAT = 'n3'
DOCUMENT_CATEGORY = 'assets'
ASSET_CATEGORIES = [u'Книги']


class TTLBooksProvider(BaseDataProvider):
    def __init__(self, root_dir):
        self.root_dir = root_dir
        filepath = os.path.abspath(os.path.join(self.root_dir, DATA_FILE))
        self.ns = Namespace('file://{0}#'.format(filepath))
        self.g = Graph().parse(filepath, format=DATA_FORMAT)

    def get_document_list(self, category):
        if category != DOCUMENT_CATEGORY:
            return

        subjects = self.g.subjects(RDF.type, self.ns.Book)
        for s in subjects:
            yield self.get_document(category, unicode(s))

        #return (Document(title=x.title, slug=x.subject)
        #        for x in self.g.triples((None, RDF.type, self.ns.Book)))

#        print 'OrgTool items:'
#        for s in g.subjects(RDF.type, orgtool.Item):
#            labels = list(g.objects(subject=s, predicate=RDFS.label))
#            label = labels[0] if labels else s
#            print ' -', label
#
#        print
#        print 'What the notary public provides:'
#        notar = list(g.subjects(RDFS.label, u'нотариус'))[0]
#        for o in g.objects(notar, orgtool.provides):
#            print ' -', list(g.objects(o, RDFS.label))[0]

    def get_document(self, category, slug):
        print 'trying', category, slug
        if category != DOCUMENT_CATEGORY:
            return

        print 'searching'

        def _plain_predicate(p):
            if '#' in p:
                return p.rpartition('#')[-1]
            else:
                return p.rpartition('/')[-1]

        slug = slug if isinstance(slug, unicode) else slug.decode('utf-8')
        #return self.get_document_list(category)
#        return self.g.subjects(RDF.type, self.ns.Book)
        subject = URIRef(slug)
        triples = self.g.triples((subject, None, None))
        pairs = ((p,o) for s,p,o in triples)
        plain_pairs = ((_plain_predicate(p),o) for p,o in pairs)
        plain_dict = dict(plain_pairs, slug=unicode(slug))

        # generating HTML (yes, it's dirty)
        html_pairs = (u'<dt>{0}</dt><dd>{1}</dd>'.format(k,v)
                      for k,v in plain_dict.items())
        body = u'<dl>{0}</dl>'.format('\n'.join(html_pairs))
        return Document(title=plain_dict['title'], slug=slug, body=body,
                        categories=ASSET_CATEGORIES)
#        return list(self.g.triples((slug, None, None)))


def configure_provider():
    conf = get_app_conf()
    root_dir = conf.x_flow.SOURCE_TTLBOOKS_ROOT
    return TTLBooksProvider(root_dir)
