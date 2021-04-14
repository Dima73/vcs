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

from . import _, PLUGIN_NAME, PLUGIN_VERSION
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigSubList, ConfigInteger, ConfigYesNo, ConfigEnableDisable
from Components.ActionMap import ActionMap
from Tools.Directories import fileExists
from Screens.InfoBarGenerics import InfoBarSeek
from Screens.ChannelSelection import ChannelSelection, ChannelContextMenu, OFF, EDIT_BOUQUET, EDIT_ALTERNATIVES, MODE_TV, MODE_RADIO, service_types_tv, FLAG_SERVICE_NEW_FOUND
from Components.ChoiceList import ChoiceEntryComponent
from Tools.BoundFunction import boundFunction
from enigma import eTimer, iServiceInformation, iPlayableService, eServiceReference, eDVBDB
from Components.Converter.Converter import Converter
from Components.Converter.ServiceInfo import ServiceInfo
from Components.Element import cached
import NavigationInstance

FLAG_SERVICE_43_AVC = 2056

WIDESCREEN = [3, 4, 7, 8, 0xB, 0xC, 0xF, 0x10]


def isMovieAspect_plugin():
	try:
		MovieAspect_plugin = config.plugins.movieaspect.enabled
	except:
		MovieAspect_plugin = None
	return MovieAspect_plugin


BOX_MODEL = "none"
BOX_NAME = ""
if fileExists("/proc/stb/info/vumodel") and not fileExists("/proc/stb/info/hwmodel") and not fileExists("/proc/stb/info/boxtype"):
	try:
		l = open("/proc/stb/info/vumodel")
		model = l.read().strip()
		l.close()
		BOX_NAME = str(model.lower())
		l.close()
		BOX_MODEL = "vuplus"
	except:
		pass
if not fileExists("/proc/stb/info/hwmodel") and fileExists("/proc/stb/info/boxtype"):
	try:
		l = open("/proc/stb/info/boxtype")
		model = l.read().strip()
		l.close()
		BOX_NAME = str(model.lower())
		l.close()
		BOX_MODEL = "all"
	except:
		pass

from VCS import InitVcsProfile, VcsInfoBar, VcsSetupScreen, VcsInfoBarKeys, VcsChoiseList, setAspect

config.plugins.VCS = ConfigSubsection()
config.plugins.VCS.enabled = ConfigEnableDisable(True)
config.plugins.VCS.restart_after_standby = ConfigYesNo(False)
config.plugins.VCS.hotkey = ConfigSelection([(x[0], x[1]) for x in VcsInfoBarKeys], "none")
config.plugins.VCS.hkaction = ConfigSelection([("switch", _("switch profiles")), ("choise", _("show choise box"))], "switch")
config.plugins.VCS.dont_use_clip = ConfigYesNo(default=BOX_NAME.startswith('et8500') and True or False)
if not BOX_NAME.startswith('et') and config.plugins.VCS.dont_use_clip.value:
	config.plugins.VCS.dont_use_clip.value = False
	config.plugins.VCS.dont_use_clip.save()
config.plugins.VCS.ext_menu = ConfigYesNo(False)
config.plugins.VCS.dvd_menu = ConfigYesNo(False)
config.plugins.VCS.media_player = ConfigYesNo(False)
config.plugins.VCS.vu_avc43 = ConfigYesNo(False)
config.plugins.VCS.vu_start_video = ConfigSelection([("no", _("no")), ("yes", _("yes")), ("yes_except", _("yes, except '4:3 PanScan'")), ("4_3_letterbox", _("use ") + _("Letterbox")), ("4_3_panscan", _("use ") + _("PanScan"))], "no")
if BOX_MODEL != "vuplus" or not config.plugins.VCS.enabled.value:
	config.plugins.VCS.vu_start_video.value = "no"
	config.plugins.VCS.vu_start_video.save()
	config.plugins.VCS.vu_avc43.value = False
	config.plugins.VCS.vu_avc43.save()
config.plugins.VCS.autoswitch_service_43 = ConfigInteger(-1)
config.plugins.VCS.autoswitch_service_169 = ConfigInteger(-1)
config.plugins.VCS.delay_switch_profile = ConfigSelection([(str(x), str(x)) for x in range(21)], "3")
config.plugins.VCS.default = ConfigInteger(-1)
config.plugins.VCS.msgtime = ConfigSelection([(str(x), str(x)) for x in range(11)], "3")
config.plugins.VCS.pfs_count = ConfigInteger(0)
config.plugins.VCS.profiles = ConfigSubList()
if config.plugins.VCS.pfs_count.value:
	for x in range(config.plugins.VCS.pfs_count.value):
		config.plugins.VCS.profiles.append(InitVcsProfile(name=_("Profile %d") % (x + 1)))
else:
	config.plugins.VCS.profiles.append(InitVcsProfile(name=_("Default Profile")))
	config.plugins.VCS.pfs_count.value = 1
	config.plugins.VCS.pfs_count.save()
	config.plugins.VCS.default.value = 0
	config.plugins.VCS.default.save()
	config.plugins.VCS.autoswitch_service_43.value = -1
	config.plugins.VCS.autoswitch_service_43.save()
	config.plugins.VCS.autoswitch_service_169.value = -1
	config.plugins.VCS.autoswitch_service_169.save()

baseDVDPlayer__init__ = None


def DVDPlayerInit():
	global baseDVDPlayer__init__
	from Screens.DVD import DVDPlayer
	if baseDVDPlayer__init__ is None:
		baseDVDPlayer__init__ = DVDPlayer.__init__
	DVDPlayer.__init__ = DVDPlayer__init__


def DVDPlayer__init__(self, session, dvd_device=None, dvd_filelist=[], args=None):
	baseDVDPlayer__init__(self, session, dvd_device, dvd_filelist, args)
	if config.plugins.VCS.dvd_menu.value:
		def showVCS():
			VcsChoiseList(session)

		self["ColorActions"] = ActionMap(["ColorActions"],
				{
					"blue": showVCS,
				}, -1)


baseMediaPlayer__init__ = None
baseMoviePlayer__init__ = None


def MediaPlayerInit():
	global baseMediaPlayer__init__, baseMoviePlayer__init__ 
	action = None
	try:
		from Plugins.Extensions.MediaPlayer.plugin import MoviePlayer
		action = 'Now'
	except ImportError:
		action = None
	if action is None:
		try:
			from Plugins.Extensions.MediaPlayer.plugin import MediaPlayer
			action = 'Old'
		except ImportError:
			action = None
	if action == 'Now':
		if baseMoviePlayer__init__ is None:
			baseMoviePlayer__init__ = MoviePlayer.__init__
		MoviePlayer.__init__ = MoviePlayer__init__
	elif action == 'Old':
		if baseMediaPlayer__init__ is None:
			baseMediaPlayer__init__ = MediaPlayer.__init__
		MediaPlayer.__init__ = MediaPlayer__init__
	else:
		pass


def MoviePlayer__init__(self, session, service):
	baseMoviePlayer__init__(self, session, service)
	if config.plugins.VCS.media_player.value:
		def showVCS():
			VcsChoiseList(session)

		self["ColorActions"] = ActionMap(["ColorActions"],
				{
					"blue": showVCS,
				}, -1)


def MediaPlayer__init__(self, session, args=None):
	baseMediaPlayer__init__(self, session, args)
	if config.plugins.VCS.media_player.value:
		def showVCS():
			VcsChoiseList(session)

		self["ColorActions"] = ActionMap(["ColorActions"],
				{
					"blue": showVCS,
				}, -1)


baseInfoBar__init__ = None
auto_vcs = None
vcsinfobar = None
base_setSeekState = None
baseServiceInfo_getBoolean = None
origChannelContextMenu__init__ = None


def newInfoBar__init__(self, session):
	baseInfoBar__init__(self, session)
	self.vcsinfobar = VcsInfoBar(session, self)


@cached
def getBoolean(self):
	service = self.source.service
	info = service and service.info()
	if not info:
		return False
	is_sd_and_not_widescreen = hasattr(self, "IS_SD_AND_NOT_WIDESCREEN") and self.type == self.IS_SD_AND_NOT_WIDESCREEN
	is_sd_and_widescreen = hasattr(self, "IS_SD_AND_WIDESCREEN") and self.type == self.IS_SD_AND_WIDESCREEN
	if config.plugins.VCS.vu_avc43.value and (self.type == self.IS_WIDESCREEN or is_sd_and_widescreen or is_sd_and_not_widescreen):
		aspect = info.getInfo(iServiceInformation.sAspect)
		video_height = info.getInfo(iServiceInformation.sVideoHeight)
		if 0 < video_height < 720 and info.getInfo(iServiceInformation.sVideoType) == 1 and aspect == 3:
			if NavigationInstance.instance:
				playref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
				if playref and eDVBDB.getInstance().getFlag(eServiceReference(playref.toString())) & FLAG_SERVICE_43_AVC:
					aspect = 1
		if self.type == self.IS_WIDESCREEN:
			return aspect in WIDESCREEN
		elif is_sd_and_widescreen:
			return video_height < 720 and aspect in WIDESCREEN
		elif is_sd_and_not_widescreen:
			return video_height < 720 and aspect not in WIDESCREEN
		return False
	else:
		return baseServiceInfo_getBoolean(self)


def autostart(reason, **kwargs):
	if reason == 0:
		global baseInfoBar__init__, auto_vcs, base_setSeekState, baseServiceInfo_getBoolean, origChannelContextMenu__init__, vcsinfobar
		if config.plugins.VCS.enabled.value:
			if config.plugins.VCS.hotkey.value != "none":
				from Screens.InfoBar import InfoBar
				if baseInfoBar__init__ is None:
					baseInfoBar__init__ = InfoBar.__init__
				InfoBar.__init__ = newInfoBar__init__
			elif "session" in kwargs and vcsinfobar is None:
				import NavigationInstance
				if NavigationInstance.instance:
					vcsinfobar = VcsInfoBar(kwargs["session"], NavigationInstance.instance)
		if "session" in kwargs and auto_vcs is None:
			session = kwargs["session"]
			from VCS import AutoVCS
			auto_vcs = AutoVCS(session)
		if fileExists("/usr/lib/enigma2/python/Screens/DVD.pyo"):
			try:
				DVDPlayerInit()
			except Exception:
				pass
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MediaPlayer/plugin.pyo") or fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MediaPlayer/plugin.pyc"):
			try:
				MediaPlayerInit()
			except Exception:
				pass
		if base_setSeekState is None:
			base_setSeekState = InfoBarSeek.setSeekState
			InfoBarSeek.setSeekState = setSeekState
			InfoBarSeek.updateAspect = updateAspect
		if BOX_MODEL == "vuplus" and baseServiceInfo_getBoolean is None:
			baseServiceInfo_getBoolean = ServiceInfo.getBoolean
			ServiceInfo.getBoolean = getBoolean
			ServiceInfo.boolean = property(getBoolean)
		if BOX_MODEL == "vuplus" and origChannelContextMenu__init__ is None:
			origChannelContextMenu__init__ = ChannelContextMenu.__init__
			ChannelContextMenu.__init__ = VCSChannelContextMenu__init__
			ChannelContextMenu.addFlag43SDservice = addFlag43SDservice
			ChannelContextMenu.removeFlag43SDservice = removeFlag43SDservice


def VCSChannelContextMenu__init__(self, session, csel):
	origChannelContextMenu__init__(self, session, csel)
	if csel.mode == MODE_TV and csel.bouquet_mark_edit == OFF and not csel.movemode:
		self.csel = csel
		current = csel.getCurrentSelection()
		current_root = csel.getRoot()
		current_sel_path = current.getPath()
		current_sel_flags = current.flags
		inBouquetRootList = current_root and current_root.getPath().find('FROM BOUQUET "bouquets.') != -1
		inBouquet = csel.getMutableList() is not None
		isPlayable = not (current_sel_flags & (eServiceReference.isMarker | eServiceReference.isDirectory | eServiceReference.isGroup))
		self.current_ref = session.nav.getCurrentlyPlayingServiceReference()
		if isPlayable and current and current.valid() and not current_sel_path:
			str_service = current.toString()
			if '%3a//' not in str_service and not str_service.rsplit(":", 1)[1].startswith("/"):
				if eDVBDB.getInstance().getFlag(eServiceReference(str_service)) & FLAG_SERVICE_43_AVC:
					self["menu"].list.insert(8, ChoiceEntryComponent(text=(_("Unmark service as 4:3 AVC/MPEG4"), boundFunction(self.removeFlag43SDservice, 1)), key="dummy"))
				elif config.plugins.VCS.vu_avc43.value and self.current_ref and self.current_ref == current:
					service = session.nav.getCurrentService()
					if service:
						info = service.info()
						if info:
							aspect = info.getInfo(iServiceInformation.sAspect)
							video_height = info.getInfo(iServiceInformation.sVideoHeight)
							if 0 < video_height < 720 and info.getInfo(iServiceInformation.sVideoType) == 1 and aspect == 3:
								self["menu"].list.insert(8, ChoiceEntryComponent(text=(_("Mark service as 4:3 AVC/MPEG4"), boundFunction(self.addFlag43SDservice, 1)), key="dummy"))


def addFlag43SDservice(self, answer=None):
	if NavigationInstance.instance:
		playref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
		if playref:
			eDVBDB.getInstance().addFlag(eServiceReference(self.csel.getCurrentSelection().toString()), FLAG_SERVICE_43_AVC)
			eDVBDB.getInstance().reloadBouquets()
			try:
				NavigationInstance.instance.pnav.navEvent(iPlayableService.evVideoSizeChanged)
			except:
				pass
	self.close()


def removeFlag43SDservice(self, answer=None):
	eDVBDB.getInstance().removeFlag(eServiceReference(self.csel.getCurrentSelection().toString()), FLAG_SERVICE_43_AVC)
	if NavigationInstance.instance:
		playref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
		if playref and playref == self.csel.getCurrentSelection():
			eDVBDB.getInstance().reloadBouquets()
			try:
				NavigationInstance.instance.pnav.navEvent(iPlayableService.evVideoSizeChanged)
			except:
				pass
	self.close()


def updateAspect(self):
	vu_start_video = config.plugins.VCS.vu_start_video.value
	if vu_start_video == "4_3_letterbox" or vu_start_video == "4_3_panscan":
		service = self.session.nav.getCurrentService()
		if service:
			serviceInfo = service.info()
			xres = serviceInfo.getInfo(iServiceInformation.sVideoWidth)
			yres = serviceInfo.getInfo(iServiceInformation.sVideoHeight)
			if xres > 0 and yres > 0:
				ratio = xres / yres
				if ratio >= 1.78:
					if vu_start_video == "4_3_letterbox":
						aspectnum = 0
					else:
						aspectnum = 1
					print "[VCS] force set video aspect ", vu_start_video
					setAspect(aspectnum)
	else:
		try:
			policy = open("/proc/stb/video/policy2", "r").read()[:-1]
			open("/proc/stb/video/policy2", "w").write(policy)
			print "[VCS] force update video aspect ", policy
		except IOError:
			pass


def setSeekState(self, state):
	prev_state = state
	service = self.session.nav.getCurrentService()
	if service is None:
		return False
	if not self.isSeekable():
		if prev_state not in (self.SEEK_STATE_PLAY, self.SEEK_STATE_PAUSE):
			prev_state = self.SEEK_STATE_PLAY
	pauseable = service.pause()
	if pauseable is None:
		prev_state = self.SEEK_STATE_PLAY
	seekstate = prev_state
	if base_setSeekState(self, state):
		if pauseable is not None:
			if seekstate[0]:
				fix_aspect = False
			elif seekstate[1]:
				fix_aspect = False
			elif seekstate[2]:
				fix_aspect = False
			else:
				fix_aspect = True
			vu_start_video = config.plugins.VCS.vu_start_video.value
			if config.plugins.VCS.enabled.value and vu_start_video != "no" and fix_aspect and not (vu_start_video == "yes_except" and config.av.policy_43.value == "panscan"):
				if isMovieAspect_plugin() is not None and config.plugins.movieaspect.enabled.value != "no":
					print "[VCS] stop - using setup plugin MovieAspect"
					return
				if not hasattr(self, "updateAspectTimer"):
					self.updateAspectTimer = eTimer()
					self.updateAspectTimer.callback.append(self.updateAspect)
				self.updateAspectTimer.start(100, True)
	return True


def show_choisebox(session, **kwargs):
	VcsChoiseList(session)


def main(session, **kwargs):
	session.open(VcsSetupScreen)


def Plugins(**kwargs):
	from Plugins.Plugin import PluginDescriptor
	desc = _("video clipping switcher") + ": " + PLUGIN_VERSION
	if config.plugins.VCS.ext_menu.value:
		return [PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart),
			PluginDescriptor(name=PLUGIN_NAME, description=desc, where=PluginDescriptor.WHERE_PLUGINMENU, icon="vcs.png", fnc=main),
			PluginDescriptor(name=_('%s:Choise List') % (PLUGIN_NAME), description=desc, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=show_choisebox)]
	else:
		return [PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart),
			PluginDescriptor(name=PLUGIN_NAME, description=desc, where=PluginDescriptor.WHERE_PLUGINMENU, icon="vcs.png", fnc=main)]
