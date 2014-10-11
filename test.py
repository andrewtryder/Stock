###
# Copyright (c) 2013-2014, spline
# All rights reserved.
#
#
###

from supybot.test import *

class OddsTestCase(PluginTestCase):
    plugins = ('Stock',)

def testStock(self):
        self.assertRegexp('bonds', 'Treasury')
        self.assertRegexp('currency USDCAD', 'USD to CAD')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:

