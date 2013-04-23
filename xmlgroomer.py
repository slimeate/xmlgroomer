#!/usr/bin/env python
# usage: xmlgroomer.py before.xml after.xml

import sys
import re
import lxml.etree as etree

groomers = []

def fix_article_type(root):
    for article_type in root.xpath("//article-categories//subj-group[@subj-group-type='heading']/subject"):
        if article_type.text == 'Clinical Trial':
            print 'changing article type from Clinical Trial to Research Article'
            article_type.text = 'Research Article'
    return root
groomers.append(fix_article_type)

def fix_date(root, pubdate):
    em_year = pubdate[:4]
    em_month = pubdate[5:7]
    em_day = pubdate[8:]
    # pubdate
    for date in root.xpath("pub-date[@pub-type='epub']"):
        xml_year = date.xpath("year")[0].text
        xml_month = date.xpath("month")[0].text
        xml_day = date.xpath("day")[0].text
        if xml_year != em_year:
            print 'changing pub year from', xml_year, 'to', em_year
            date.xpath("year")[0].text = em_year
        if xml_month != em_month:
            print 'changing pub month from', xml_month, 'to', str(int(em_month))
            date.xpath("month")[0].text = str(int(em_month))
        if xml_day != em_day:
            print 'changing pub day from', xml_day, 'to', str(int(em_day))
            date.xpath("day")[0].text = str(int(em_day))
    # collection month and year
    for coll in root.xpath("//pub-date[@pub-type='collection']"):
        coll_year = coll.xpath("year")[0].text
        coll_month = coll.xpath("month")[0].text
        if coll_year != em_year:
            print 'changing collection year from', coll_year, 'to', em_year
            coll.xpath("year")[0].text = em_year
        if coll_month != em_month:
            print 'changing collection month from', coll_month, 'to', str(int(em_month))
            coll.xpath("month")[0].text = str(int(em_month))
    return root
#groomers.append(fix_date)

def fix_journal_ref(root):
    for link in root.xpath("//mixed-citation[@publication-type='journal']/ext-link"):
        print 'adding comment tag around journal reference link'
        parent = link.getparent()
        index = parent.index(link)
        comment = etree.Element('comment')
        comment.append(link)
        previous = parent.getchildren()[index-1]
        if previous.tail:
            comment.text = previous.tail
            previous.tail = ''
        parent.insert(index, comment)
    return root
groomers.append(fix_journal_ref)

def fix_url(root):
    for link in root.xpath("//ext-link"):
        h = '{http://www.w3.org/1999/xlink}href'
        assert h in link.attrib  # error: ext-link does not have href
        # remove whitespace
        if re.search(r'\s', link.attrib[h]):
            new_link = re.sub(r'\s', r'', link.attrib[h])
            print 'changing link from', link.attrib[h], 'to', new_link
            link.attrib[h] = new_link
        # prepend dx.doi.org if url is only a doi
        if re.match(r'http://10.[0-9]{4}', link.attrib[h]):
            new_link = link.attrib[h].replace('http://', 'http://dx.doi.org/')
            print 'changing link from', link.attrib[h], 'to', new_link
            link.attrib[h] = new_link
    return root
groomers.append(fix_url)

def fix_comment(root):
    for comment in root.xpath("//comment"):
        if comment.tail:
            print 'removing period after comment end tag'
            comment.tail = re.sub(r'^\.', r'', comment.tail)
    return root
groomers.append(fix_comment)

def fix_provenance(root):
    for prov in root.xpath("//author-notes//fn[@fn-type='other']"):
        if prov.xpath("p/bold")[0].text == 'Provenance:':
            print 'moving provenance from author-notes to fn-group after references'
            fngroup = etree.Element('fn-group')
            fngroup.append(prov)
            reflist = root.xpath("//ref-list")[0]
            parent = reflist.getparent()
            parent.insert(parent.index(reflist) + 1, fngroup)
    return root
groomers.append(fix_provenance)

def fix_empty_element(root):
    for element in root.iterdescendants():
        if not element.text and not element.attrib and not element.getchildren():
            print 'removing empty element', element.tag
            element.getparent().remove(element)        
    return root
groomers.append(fix_empty_element)

if __name__ == '__main__':
    if len(sys.argv) == 3:
        e = etree.parse(sys.argv[1])
        root = e.getroot()
        for groomer in groomers:
            root = groomer(root)
        e.write(sys.argv[2], xml_declaration = True, encoding = 'UTF-8')
        print 'done'
    else:
        print 'usage: xmlgroomer.py before.xml after.xml'
