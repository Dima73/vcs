#
# Video ClipModes Switcher Plugin for Enigma2
# Coded by vlamo (c) 2012
#
# This module is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program; if not, write to the Free Software Foundation, Inc., 59
# Temple Place, Suite 330, Boston, MA 0.1.2-1307 USA
###############################################################################

from Components.Language import language
import os, gettext

PLUGIN_NAME = "VCS"
PLUGIN_VERSION = "2.5"
PLUGIN_PATH = os.path.dirname( __file__ )

def localeInit():
	os.environ["LANGUAGE"] = language.getLanguage()[:2]
	gettext.bindtextdomain(PLUGIN_NAME, "%s/locale"%(PLUGIN_PATH))

def _(txt):
	t = gettext.dgettext(PLUGIN_NAME, txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)
