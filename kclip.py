import datetime
import time
import codecs
import re
#from pprint import pprint

__all__ = ['parse', 'Book', 'Clip', 'ParseError']

DEBUG = True

class ParseError(ValueError):
    """ This is not used consistently """
    pass

class Book(object):
    """ 
    Encapsulate the concept of a book/article on the Kindle.

    A book will have one or more clippings and simplifies access to filtering
    only specific clipping types, or sorting by time/location.
    """

    def __init__(self, title, attribution):
        self.title = title
        self.attribution = attribution
        self.clippings = []

    def by_location(self, reverse=False, clip_type=None):
        """
        Even though location is a string, it's consistent within a book.
        e.g. all clippings will be prefixed by "Loc." or "Page"
        """
        filtered_set = self.clips_of_type(clip_type)
        filtered_set.sort(key=lambda x: x.location, reverse=reverse)
        return filtered_set

    def by_time(self, reverse=False, clip_type=None):
        filtered_set = self.clips_of_type(clip_type)
        filtered_set.sort(key=lambda x: x.datetime, reverse=reverse)
        return filtered_set

    def clips_of_type(self, clip_type=None):
        """ Only return clips that match clip_type """
        return filter(lambda x: x.clip_type == clip_type if clip_type else True,
                      self.clippings)

    def __repr__(self):
        c_repr = u'<Book "%s" by "%s">' % (self.title, self.attribution or "Unknown")
        return c_repr.encode('utf-8')


class Clip(object):
    DATE_FORMAT = '%F %R'

    def __init__(self, book, clip_type, location, datetime, notes):
        self.clip_type = clip_type
        self.location = location
        self.datetime = datetime
        self.notes = notes.strip() if notes.strip() else ''

    def display(self):
        c_str = u'%s, %s\n%s\n' % (self.location,
                self.datetime.strftime(self.DATE_FORMAT), self.notes)
        return c_str.encode('utf-8')


    def __str__(self):
        c_str = u'<%s at %s, %s, "%s">' % (self.clip_type,
                self.datetime.strftime(self.DATE_FORMAT), self.location, self.notes[:10] + '...')
        return c_str.encode('utf-8')

    def __repr__(self):
        # Don't truncate 
        c_repr = u'<%s at %s, %s, "%s">' % (self.clip_type,
                self.datetime.strftime(self.DATE_FORMAT), self.location, self.notes)
        return c_repr.encode('utf-8')

KINDLE_FIRST_LINE_NOISE = "\xef\xbb\xbf"
KINDLE_DIVIDER = '='*10
KINDLE_DATE_FORMAT = '%A, %B %d, %Y, %I:%M %p'
# Not sure about this one, there are some versions online of 'My Clippings.txt'
# that display second and are missing a comma.
KINDLE_DATE_FORMAT_W_SECOND = '%A, %B %d, %Y %I:%M:%S %p'
LINE_BREAK = "\r\n"

def parse_title(title_meta):
    """
    >>> parse_title('Bertrand Russell - Proposed Roads To Freedom')
    'Bertrand Russell - Proposed Roads To Freedom'
    >>> parse_title('Goethe_s_opinions_on_the_world_mankind_l (Johann Wolfgang von Goethe)')
    'Goethe_s_opinions_on_the_world_mankind_l'
    """
    stripped = title_meta.strip()
    if stripped[-1] == ')':
        return stripped[:title_meta.rfind(' (')]
    return stripped

def parse_attribution(title_meta):
    """
    >>> parse_attribution('Goethe_s_opinions_on_the_world_mankind_l (Johann Wolfgang von Goethe)')
    'Johann Wolfgang von Goethe'
    """
    if title_meta.strip()[-1] == ')':
        return title_meta[title_meta.rfind(' (')+2:title_meta.rfind(')')]
    return None

def parse_type(meta):
    """
    >>> parse_type('- Highlight Loc. 503  | Added on Wednesday, January 05, 2011, 12:57 AM')
    'Highlight'
    >>> parse_type('- Bookmark Loc. 3426  | Added on Sunday, December 19, 2010, 08:15 PM')
    'Bookmark'
    >>> parse_type('- Note Loc. 1625  | Added on Thursday, November 22, 2012, 12:37 PM')
    'Note'
    """
    type_str = meta[2:meta.find('|')]
    allowed_types = ['Bookmark', 'Note', 'Highlight']
    for t in allowed_types:
        if type_str.find(t) == 0:
            return t
    raise ParseError("parse error: expected Note, Highlight or Bookmark")

def parse_location(meta):
    """
    >>> parse_location('- Note on Page 29 | Added on Thursday, November 22, 2012, 12:39 PM')
    'Page 29'
    >>> parse_location('- Note Loc. 1625  | Added on Thursday, November 22, 2012, 12:37 PM')
    'Loc. 1625'
    """
    m=re.match(r'- \w+ (Loc.|on Page) (\d+(-\d+)?)\s+\|',meta)
    if m:
        loc = ' '.join(m.groups()[:2])
        if loc[:3] == 'on ':
            return loc[3:]
        return loc
    else:
        print meta
        raise ParseError("parse error. Expected 'Loc.' or 'on Page")

def parse_datetime(meta):
    """
    >>> parse_datetime('- Highlight Loc. 503  | Added on Wednesday, January 05, 2011, 12:57 AM')
    datetime.datetime(2011, 1, 5, 0, 57, 0, 2)
    >>> parse_datetime('- Bookmark Loc. 3426  | Added on Sunday, December 19, 2010, 08:15 PM')
    datetime.datetime(2010, 12, 19, 20, 15, 0, 6)
    >>> parse_datetime('- Note Loc. 1625  | Added on Thursday, November 22, 2012, 12:37 PM')
    datetime.datetime(2012, 11, 22, 12, 37, 0, 3)
    """
    text_date = meta[meta.find('Added on ')+9:]
    try:
        return datetime.datetime(*time.strptime(text_date, KINDLE_DATE_FORMAT)[:-2])
    except ValueError:
        return datetime.datetime(*time.strptime(text_date, KINDLE_DATE_FORMAT_W_SECOND)[:-2])

DEFAULT_SYNTAX = {
      'title': parse_title,
      'attribution': parse_attribution,
      'clip_type': parse_type,
      'location': parse_location,
      'datetime': parse_datetime
      }

def _parse_record(raw_content, parsers=DEFAULT_SYNTAX):
    prelude, meta, _blank_line, notes = raw_content

    title = parsers['title'](prelude)
    attribution = parsers['attribution'](prelude)
    clip_type = parsers['clip_type'](meta)
    location = parsers['location'](meta)
    datetime = parsers['datetime'](meta)

    book = Book(title, attribution)
    clip = Clip(book, clip_type, location, datetime, notes)
    return book, clip


def parse(filename, syntax=DEFAULT_SYNTAX):
    """
    Main method for parsing 'My Clippings.txt'

    Pass it a filename.

    You can override the parsing of each part of a clipping record by
    parsing a dictionary of functions to the syntax parameter, similar to
    DEFAULT_SYNTAX.

    Returns a dictionary of Books, keyed on title. Each Book has a series
    of clippings.
    """
    books = {}
    clip_file = codecs.open(filename)

    # get magic cookie
    magic = clip_file.read(3)
    try:
        assert magic == KINDLE_FIRST_LINE_NOISE
    except AssertionError:
        print "Warning: Expected preamble missing in %s" % filename
        clip_file.seek(0)

    record = list()
    for line in clip_file:
        line = line.decode( 'utf-8' )
        if line.strip() == KINDLE_DIVIDER:
            book, clip = _parse_record(record, parsers=syntax)
            book = books.get(book.title, book)
            book.clippings.append(clip)
            books[book.title] = book
            record = list()
        else:
            record.append(line.strip())
    clip_file.close()
    return books

if __name__ == "__main__":
    import sys
    import doctest

    doctest.testmod()

    if DEBUG == True:
        books = parse(sys.argv[1])
        print '%d books with %d clippings total' % (
                len(books),
                sum([len(b.clippings) for b in books.values()])
                )
        for book in books:
            print book
        import pdb; pdb.set_trace()


