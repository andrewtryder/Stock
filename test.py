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
        self.assertRegexp('gold', 'Gold')
        self.assertRegexp('googlequote GOOG', 'Google')
        self.assertRegexp('grains', 'Corn')
        self.assertRegexp('indices', 'Dow Jones')
        self.assertRegexp('intlindicies', 'HANG SENG')
        self.assertRegexp('metals', 'Gold')
        self.assertRegexp('oil', 'Crude Oil')
        self.assertRegexp('stock GOOG', 'Google')
        self.assertRegexp('symbolsearch Google', 'Google')
        self.assertRegexp('yahooquote GOOG', 'Google')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:

