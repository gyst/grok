##############################################################################
#
# Copyright (c) 2006-2007 Zope Corporation and Contributors.
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
"""Grok utility functions.
"""

import urllib

import zope.location.location
from zope import component
from zope import interface
from zope.traversing.browser.interfaces import IAbsoluteURL
from zope.traversing.browser.absoluteurl import _safe as SAFE_URL_CHARACTERS

from zope.security.checker import NamesChecker, defineChecker
from zope.security.interfaces import IPermission

from martian.error import GrokError
from martian.util import class_annotation

# BBB backwards-compatibility imports (in case somebody wrote custom
# grokkers that use these utility functions)
from grokcore.component.util import check_adapts
from grokcore.component.util import determine_class_directive
from grokcore.component.util import public_methods_from_class
from grokcore.component.util import sort_components
from grokcore.component.util import determine_module_component
from grokcore.component.util import determine_class_component

def make_checker(factory, view_factory, permission, method_names=None):
    """Make a checker for a view_factory associated with factory.

    These could be one and the same for normal views, or different
    in case we make method-based views such as for JSON and XMLRPC.
    """
    if method_names is None:
        method_names = ['__call__']
    if permission is not None:
        check_permission(factory, permission)
    if permission is None or permission == 'zope.Public':
        checker = NamesChecker(method_names)
    else:
        checker = NamesChecker(method_names, permission)
    defineChecker(view_factory, checker)

def check_permission(factory, permission):
    """Check whether a permission is defined.

    If not, raise error for factory.
    """
    if component.queryUtility(IPermission,
                              name=permission) is None:
       raise GrokError('Undefined permission %r in %r. Use '
                       'grok.Permission first.'
                       % (permission, factory), factory)

def get_default_permission(factory):
    """Determine the default permission for a view.

    There can be only 0 or 1 default permission.
    """
    permissions = class_annotation(factory, 'grok.require', [])
    if not permissions:
        return None
    if len(permissions) > 1:
        raise GrokError('grok.require was called multiple times in '
                        '%r. It may only be set once for a class.'
                        % factory, factory)

    result = permissions[0]
    return result

def url(request, obj, name=None, data={}):
    url = component.getMultiAdapter((obj, request), IAbsoluteURL)()
    if name is not None:
        url += '/' + urllib.quote(name.encode('utf-8'), SAFE_URL_CHARACTERS)
    if data:
        for k,v in data.items():
            if isinstance(v, unicode):
                data[k] = v.encode('utf-8')
            if isinstance(v, (list, set, tuple)):
                data[k] = [isinstance(item, unicode) and item.encode('utf-8') 
                or item for item in v]
        url += '?' + urllib.urlencode(data, doseq=True)
    return url

def safely_locate_maybe(obj, parent, name):
    """Set an object's __parent__ (and __name__) if the object's
    __parent__ attribute doesn't exist yet or is None.

    If the object provides ILocation, __parent__ and __name__ will be
    set directly.  A location proxy will be returned otherwise.
    """
    if getattr(obj, '__parent__', None) is not None:
        return obj
    # This either sets __parent__ or wraps 'obj' in a LocationProxy
    return zope.location.location.located(obj, parent, name)

def applySkin(request, skin, skin_type):
    """Change the presentation skin for this request.
    """
    # Remove all existing skin declarations (commonly the default skin).
    ifaces = [iface for iface in interface.directlyProvidedBy(request)
              if not skin_type.providedBy(iface)]
    # Add the new skin.
    ifaces.append(skin)
    interface.directlyProvides(request, *ifaces)
