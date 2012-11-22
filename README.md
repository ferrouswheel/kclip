kclip
=====

Python module for reading a Kindle's `My Clippings.txt` file. These contain
highlights and notes made by the user while reading a book on the Kindle platform.
Clippings get synced and are accessible online if you are reading an ebook
bought from Amazon. However, if you sideload stuff by USB you miss this feature.
Having clippings on Amazon's web site is also not particularly useful. Amazon make
some great products and have many strengths, but designing clean consistent UIs
does not appear to be one of them.

## Why another module??

The My Clippings format is pretty simple, and there are many other implementations
out there, so why create another? My reasoning is that they are either:

* custom (and flaky) gist scripts to transform the data to another format, or
* they treat all notes as [individual](https://github.com/tswicegood/pyKindle)
  [entries](https://github.com/albins/kindle-clippings-parser) in list. There
  may be some cases where this is what you want, but I think clippings are more
  useful aggregated by article/book; or
* they [seem more complicated than necessary](https://github.com/gfranxman/Kindle-Clippings-Parser), or
* they [use weirdCamelCase](https://github.com/rydjones/Kindle-Clippings-Export)

All the above libraries were useful in understanding the format, so big thanks!

The aim of this module is to be simple. For me, this is just step
one for getting my clippings into evernote (I know about
[ClippingConverter](http://clippingsconverter.com/), but
since they sent me my account password in plaintext, there's no way I'm
trusting access to my evernote account to them!)

I've also opted for a solitary module, and not a package, because it's easier
to just take the module and use it in a custom script... in fact, it's simple enough
to just replace main() with your post processing. That may change
if I get around to packaging it.

## Usage

```python
>>> from kclip import parse
>>> books = parse('/path/to/My Clippings.txt')
>>> print books
{u'Proposed Roads To Freedom':
    <Book "Proposed Roads To Freedom" by "Bertrand Russell">,
 u'Goethe_s_opinions_on_the_world_mankind_l':
     <Book "Goethe_s_opinions_on_the_world_mankind_l" by "Johann Wolfgang von Goethe">}
>>> prtf = books.values()[0] # Proposed Roads to Freedom
>>> print prtf.clippings 
[<Highlight at 2012-11-22 12:35, Loc. 1622-23, "world had ...">,
 <Note at 2012-11-22 12:36, Loc. 1624, "this is a ...">,
 <Highlight at 2012-11-22 12:37, Loc. 1625, "world. The...">,
 <Note at 2012-11-22 12:37, Loc. 1625, "a shared n...">]
>>> print prtf.by_location(clip_type='Note') # Sort by location
[<Note at 2012-11-22 12:36, Loc. 1624, "this is a ...">,
 <Note at 2012-11-22 12:37, Loc. 1625, "a shared n...">]
>>> print prtf.by_time(clip_type='Highlight', reverse=True) # Sort by time
[<Highlight at 2012-11-22 12:37, Loc. 1625, "world. The...">,
 <Highlight at 2012-11-22 12:35, Loc. 1622-23, "world had ...">]
>>> prtf.clippings[0].notes
u'world had developed as Marx expected, the kind of internationalism which he foresaw might have inspired a universal social revolution. Russia, which devel-'
```

