"""
Models can determine how they want to be traversed by using the
``@grok.traverse`` decorator:

  >>> import grok
  >>> from grok.ftests.traversal.modeltraverse import Herd
  >>> grok.grok('grok.ftests.traversal.modeltraverse')
  >>> getRootFolder()["herd"] = Herd()

  >>> from zope.testbrowser.testing import Browser
  >>> browser = Browser()
  >>> browser.handleErrors = False
  >>> browser.open("http://localhost/herd/manfred")
  >>> print browser.contents
  <html>
  <body>
  <h1>Hello, Manfred!</h1>
  </body>
  </html>

  >>> browser.open("http://localhost/herd/ellie")
  >>> print browser.contents
  <html>
  <body>
  <h1>Hello, Ellie!</h1>
  </body>
  </html>

"""
import grok

class Herd(grok.Model):

    @grok.traverse
    def getMammoth(self, name):
        return Mammoth(name)

class Mammoth(grok.Model):

    def __init__(self, name):
        self.name = name

grok.context(Mammoth)
index = grok.PageTemplate("""\
<html>
<body>
<h1>Hello, <span tal:replace="context/name/title" />!</h1>
</body>
</html>
""")