##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Grok
"""
from zope import component
from zope.component.interfaces import IDefaultViewName
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.app.component.site import LocalSiteManager

import martian
from martian import scan
from martian.error import GrokError
from martian.util import determine_module_context

import grok
import grokcore.component.grokkers
from grok import components, meta, templatereg

_bootstrapped = False
def bootstrap():
    # register a subscriber for when grok.Sites are added to make them
    # into Zope 3 sites
    component.provideHandler(addSiteHandler)

    # now grok the grokkers
    martian.grok_module(scan.module_info_from_module(meta), the_module_grokker)
    martian.grok_module(scan.module_info_from_module(grokcore.component.grokkers),
                        the_module_grokker)

@component.adapter(grok.Site, grok.IObjectAddedEvent)
def addSiteHandler(site, event):
    sitemanager = LocalSiteManager(site)
    # LocalSiteManager creates the 'default' folder in its __init__.
    # It's not needed anymore in new versions of Zope 3, therefore we
    # remove it
    del sitemanager['default']
    site.setSiteManager(sitemanager)

# add a cleanup hook so that grok will bootstrap itself again whenever
# the Component Architecture is torn down.
def resetBootstrap():
    global _bootstrapped
    # we need to make sure that the grokker registry is clean again
    the_module_grokker.clear()
    _bootstrapped = False
from zope.testing.cleanup import addCleanUp
addCleanUp(resetBootstrap)


def do_grok(dotted_name):
    global _bootstrapped
    if not _bootstrapped:
        bootstrap()
        _bootstrapped = True
    martian.grok_dotted_name(dotted_name, the_module_grokker)

def grok_component(name, component,
                   context=None, module_info=None, templates=None):
    return the_multi_grokker.grok(name, component,
                                  context=context,
                                  module_info=module_info,
                                  templates=templates)

def prepare_grok(name, module, kw):
    module_info = scan.module_info_from_module(module)

    # XXX hardcoded in here which base classes are possible contexts
    # this should be made extensible
    possible_contexts = martian.scan_for_classes(module, [grok.Model,
                                                          grok.Container])
    context = determine_module_context(module_info, possible_contexts)

    kw['context'] = context
    kw['module_info'] = module_info
    kw['templates'] = templatereg.TemplateRegistry()

def finalize_grok(name, module, kw):
    module_info = kw['module_info']
    templates = kw['templates']
    unassociated = list(templates.listUnassociated())
    if unassociated:
        raise GrokError("Found the following unassociated template(s) when "
                        "grokking %r: %s.  Define view classes inheriting "
                        "from grok.View to enable the template(s)."
                        % (module_info.dotted_name,
                           ', '.join(unassociated)), module_info)

the_multi_grokker = martian.MetaMultiGrokker()
the_module_grokker = martian.ModuleGrokker(the_multi_grokker,
                                           prepare=prepare_grok,
                                           finalize=finalize_grok)
