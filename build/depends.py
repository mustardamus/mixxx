# -*- coding: utf-8 -*-

import os
from . import util
from .mixxx import Dependence, Feature
import SCons.Script as SCons


class PortAudio(Dependence):

    def configure(self, build, conf):
        if not conf.CheckLib('portaudio'):
            raise Exception(
                'Did not find libportaudio.a, portaudio.lib, or the PortAudio-v19 development header files.')
        elif build.platform_is_linux:
            build.env.ParseConfig('pkg-config portaudio-2.0 --silence-errors --cflags --libs')

        if build.platform_is_windows and build.static_dependencies:
            conf.CheckLib('advapi32')

    def sources(self, build):
        return ['soundio/sounddeviceportaudio.cpp']


class PortMIDI(Dependence):

    def configure(self, build, conf):
        # Check for PortTime
        libs = ['porttime', 'libporttime']
        headers = ['porttime.h']

        # Depending on the library configuration PortTime might be statically
        # linked with PortMidi. We treat either presence of the lib or the
        # header as success.
        if not conf.CheckLib(libs) and not conf.CheckHeader(headers):
            raise Exception("Did not find PortTime or its development headers.")

        # Check for PortMidi
        libs = ['portmidi', 'libportmidi']
        headers = ['portmidi.h']
        if build.platform_is_windows and build.static_dependencies:
            conf.CheckLib('advapi32')
        if build.platform_is_windows:
            # We have this special branch here because on Windows we might want
            # to link PortMidi statically which we don't want to do on other
            # platforms.
            # TODO(rryan): Remove this? Don't want to break anyone but the
            # static/dynamic choice should be made by the whether the .a is an
            # import library for a shared library or a static library.
            libs.append('portmidi_s')

        if not conf.CheckLib(libs) or not conf.CheckHeader(headers):
            raise Exception("Did not find PortMidi or its development headers.")

    def sources(self, build):
        return ['controllers/midi/portmidienumerator.cpp', 'controllers/midi/portmidicontroller.cpp']


class OpenGL(Dependence):

    def configure(self, build, conf):
        if build.platform_is_osx:
            build.env.AppendUnique(FRAMEWORKS='OpenGL')

        # Check for OpenGL (it's messy to do it for all three platforms).
        if (not conf.CheckLib('GL') and
                not conf.CheckLib('opengl32') and
                not conf.CheckCHeader('OpenGL/gl.h') and
                not conf.CheckCHeader('GL/gl.h')):
            raise Exception('Did not find OpenGL development files')

        if (not conf.CheckLib('GLU') and
                not conf.CheckLib('glu32') and
                not conf.CheckCHeader('OpenGL/glu.h')):
            raise Exception('Did not find GLU development files')


class SecurityFramework(Dependence):
    """The iOS/OS X security framework is used to implement sandboxing."""
    def configure(self, build, conf):
        if not build.platform_is_osx:
            return
        build.env.Append(CPPPATH='/System/Library/Frameworks/Security.framework/Headers/')
        build.env.Append(LINKFLAGS='-framework Security')


class CoreServices(Dependence):
    def configure(self, build, conf):
        if not build.platform_is_osx:
            return
        build.env.Append(CPPPATH='/System/Library/Frameworks/CoreServices.framework/Headers/')
        build.env.Append(LINKFLAGS='-framework CoreServices')

class IOKit(Dependence):
    """Used for battery measurements and controlling the screensaver on OS X and iOS."""
    def configure(self, build, conf):
        if not build.platform_is_osx:
            return
        build.env.Append(
            CPPPATH='/System/Library/Frameworks/IOKit.framework/Headers/')
        build.env.Append(LINKFLAGS='-framework IOKit')

class UPower(Dependence):
    """UPower is used to get battery measurements on Linux."""
    def configure(self, build, conf):
        if not build.platform_is_linux:
            return
        build.env.ParseConfig(
                'pkg-config upower-glib --silence-errors --cflags --libs')

class OggVorbis(Dependence):

    def configure(self, build, conf):
        libs = ['libvorbisfile', 'vorbisfile']
        if not conf.CheckLib(libs):
            Exception('Did not find libvorbisfile.a, libvorbisfile.lib, '
                      'or the libvorbisfile development headers.')

        libs = ['libvorbis', 'vorbis']
        if not conf.CheckLib(libs):
            raise Exception(
                'Did not find libvorbis.a, libvorbis.lib, or the libvorbis development headers.')

        libs = ['libogg', 'ogg']
        if not conf.CheckLib(libs):
            raise Exception(
                'Did not find libogg.a, libogg.lib, or the libogg development headers')

        # libvorbisenc only exists on Linux, OSX and mingw32 on Windows. On
        # Windows with MSVS it is included in vorbisfile.dll. libvorbis and
        # libogg are included from build.py so don't add here.
        if not build.platform_is_windows or build.toolchain_is_gnu:
            vorbisenc_found = conf.CheckLib(['libvorbisenc', 'vorbisenc'])
            if not vorbisenc_found:
                raise Exception(
                    'Did not find libvorbisenc.a, libvorbisenc.lib, or the libvorbisenc development headers.')

    def sources(self, build):
        return ['sources/soundsourceoggvorbis.cpp']

class SndFile(Dependence):

    def configure(self, build, conf):
        if not conf.CheckLib(['sndfile', 'libsndfile', 'libsndfile-1']):
            raise Exception(
                "Did not find libsndfile or it\'s development headers")
        build.env.Append(CPPDEFINES='__SNDFILE__')
        if conf.CheckDeclaration('SFC_SET_COMPRESSION_LEVEL', '#include "sndfile.h"'):
            build.env.Append(CPPDEFINES='SFC_SUPPORTS_SET_COMPRESSION_LEVEL')

        if build.platform_is_windows and build.static_dependencies:
            build.env.Append(CPPDEFINES='FLAC__NO_DLL')
            conf.CheckLib('g72x')

    def sources(self, build):
        return ['sources/soundsourcesndfile.cpp']


class FLAC(Dependence):
    def configure(self, build, conf):
        if not conf.CheckHeader('FLAC/stream_decoder.h'):
            raise Exception('Did not find libFLAC development headers')
        libs = ['libFLAC', 'FLAC']
        if not conf.CheckLib(libs):
            raise Exception('Did not find libFLAC development libraries')

        if build.platform_is_windows and build.static_dependencies:
            build.env.Append(CPPDEFINES='FLAC__NO_DLL')

    def sources(self, build):
        return ['sources/soundsourceflac.cpp',]


class Qt(Dependence):
    DEFAULT_QT4DIRS = {'linux': '/usr/share/qt4',
                       'bsd': '/usr/local/lib/qt4',
                       'osx': '/Library/Frameworks',
                       'windows': 'C:\\qt\\4.6.0'}

    DEFAULT_QT5DIRS64 = {'linux': '/usr/lib/x86_64-linux-gnu/qt5',
                         'osx': '/Library/Frameworks',
                         'windows': 'C:\\qt\\5.11.1'}

    DEFAULT_QT5DIRS32 = {'linux': '/usr/lib/i386-linux-gnu/qt5',
                         'osx': '/Library/Frameworks',
                         'windows': 'C:\\qt\\5.11.1'}

    @staticmethod
    def qt5_enabled(build):
        return int(util.get_flags(build.env, 'qt5', 1))

    @staticmethod
    def uic(build):
        qt5 = Qt.qt5_enabled(build)
        return build.env.Uic5 if qt5 else build.env.Uic4

    @staticmethod
    def find_framework_libdir(qtdir, qt5):
        # Try pkg-config on Linux
        import sys
        if sys.platform.startswith('linux'):
            if any(os.access(os.path.join(path, 'pkg-config'), os.X_OK) for path in os.environ["PATH"].split(os.pathsep)):
                import subprocess
                try:
                    if qt5:
                        qtcore = "Qt5Core"
                    else:
                        qtcore = "QtCore"
                    core = subprocess.Popen(["pkg-config", "--variable=libdir", qtcore], stdout = subprocess.PIPE).communicate()[0].rstrip().decode()
                finally:
                    if os.path.isdir(core):
                        return core

        for d in (os.path.join(qtdir, x) for x in ['', 'Frameworks', 'lib']):
            core = os.path.join(d, 'QtCore.framework')
            if os.path.isdir(core):
                return d
        return None

    @staticmethod
    def enabled_modules(build):
        qt5 = Qt.qt5_enabled(build)
        qt_modules = [
            # Keep alphabetized.
            'QtCore',
            'QtGui',
            'QtNetwork',
            'QtOpenGL',
            'QtScript',
            'QtScriptTools',
            'QtSql',
            'QtSvg',
            'QtTest',
            'QtXml',
        ]
        if qt5:
            qt_modules.extend([
                # Keep alphabetized.
                'QtConcurrent',
                'QtWidgets',
            ])
            if build.platform_is_windows:
                qt_modules.extend([
                    # Keep alphabetized.
                    'QtAccessibilitySupport',
                    'QtEventDispatcherSupport',
                    'QtFontDatabaseSupport',
                    'QtThemeSupport',
                    'QtWindowsUIAutomationSupport',
                ])
        return qt_modules

    @staticmethod
    def enabled_imageformats(build):
        qt5 = Qt.qt5_enabled(build)
        qt_imageformats = [
            'qgif', 'qico', 'qjpeg',  'qmng', 'qtga', 'qtiff', 'qsvg'
        ]
        if qt5:
            qt_imageformats.extend(['qdds', 'qicns', 'qjp2', 'qwbmp', 'qwebp'])
        return qt_imageformats

    def satisfy(self):
        pass

    def configure(self, build, conf):
        qt_modules = Qt.enabled_modules(build)

        qt5 = Qt.qt5_enabled(build)
        # Emit various Qt defines
        build.env.Append(CPPDEFINES=['QT_TABLET_SUPPORT'])

        if build.static_qt:
            build.env.Append(CPPDEFINES='QT_NODLL')
        else:
            build.env.Append(CPPDEFINES='QT_SHARED')

        if qt5:
            # Enable qt4 support.
            build.env.Append(CPPDEFINES='QT_DISABLE_DEPRECATED_BEFORE')

        # Set qt_sqlite_plugin flag if we should package the Qt SQLite plugin.
        build.flags['qt_sqlite_plugin'] = util.get_flags(
            build.env, 'qt_sqlite_plugin', 0)

        # Link in SQLite library if Qt is compiled statically
        if build.platform_is_windows and build.static_dependencies \
           and build.flags['qt_sqlite_plugin'] == 0 :
            conf.CheckLib('sqlite3');

        # Enable Qt include paths
        if build.platform_is_linux:
            if qt5 and not conf.CheckForPKG('Qt5Core', '5.0'):
                raise Exception('Qt >= 5.0 not found')
            elif not qt5 and not conf.CheckForPKG('QtCore', '4.6'):
                raise Exception('QT >= 4.6 not found')

            qt_modules.extend(['QtDBus'])
            # This automatically converts QtXXX to Qt5XXX where appropriate.
            if qt5:
                build.env.EnableQt5Modules(qt_modules, debug=False)
            else:
                build.env.EnableQt4Modules(qt_modules, debug=False)

            if qt5 and build.architecture_is_x86:
                # Note that -reduce-relocations is enabled by default in Qt5.
                # So we must build the Mixxx *executable* with position
                # independent code. -pie / -fPIE must not be used, and Clang
                # -flto must not be used when producing ELFs (i.e. on Linux).
                # http://lists.qt-project.org/pipermail/development/2012-January/001418.html
                # https://github.com/qt/qtbase/blob/c5307203f5c0b0e588cc93e70764c090dd4c2ce0/dist/changes-5.4.2#L37-L45
                # https://codereview.qt-project.org/#/c/111787/
                # https://gcc.gnu.org/bugzilla/show_bug.cgi?id=65886#c30
                build.env.Append(CCFLAGS='-fPIC')

        elif build.platform_is_bsd:
            build.env.Append(LIBS=qt_modules)
            include_paths = ['$QTDIR/include/%s' % module
                             for module in qt_modules]
            build.env.Append(CPPPATH=include_paths)
        elif build.platform_is_osx:
            qtdir = build.env['QTDIR']
            build.env.Append(
                LINKFLAGS=' '.join('-framework %s' % m for m in qt_modules)
            )
            framework_path = Qt.find_framework_libdir(qtdir, qt5)
            if not framework_path:
                raise Exception(
                    'Could not find frameworks in Qt directory: %s' % qtdir)
            # Necessary for raw includes of headers like #include <qobject.h>
            build.env.Append(CPPPATH=[os.path.join(framework_path, '%s.framework' % m, 'Headers')
                                      for m in qt_modules])
            # Framework path needs to be altered for CCFLAGS as well since a
            # header include of QtCore/QObject.h looks for a QtCore.framework on
            # the search path and a QObject.h in QtCore.framework/Headers.
            build.env.Append(CCFLAGS=['-F%s' % os.path.join(framework_path)])
            build.env.Append(LINKFLAGS=['-F%s' % os.path.join(framework_path)])

            # Copied verbatim from qt4.py and qt5.py.
            # TODO(rryan): Get our fixes merged upstream so we can use qt4.py
            # and qt5.py for OS X.
            qt4_module_defines = {
                'QtScript'   : ['QT_SCRIPT_LIB'],
                'QtSvg'      : ['QT_SVG_LIB'],
                'Qt3Support' : ['QT_QT3SUPPORT_LIB','QT3_SUPPORT'],
                'QtSql'      : ['QT_SQL_LIB'],
                'QtXml'      : ['QT_XML_LIB'],
                'QtOpenGL'   : ['QT_OPENGL_LIB'],
                'QtGui'      : ['QT_GUI_LIB'],
                'QtNetwork'  : ['QT_NETWORK_LIB'],
                'QtCore'     : ['QT_CORE_LIB'],
            }
            qt5_module_defines = {
                'QtScript'   : ['QT_SCRIPT_LIB'],
                'QtSvg'      : ['QT_SVG_LIB'],
                'QtSql'      : ['QT_SQL_LIB'],
                'QtXml'      : ['QT_XML_LIB'],
                'QtOpenGL'   : ['QT_OPENGL_LIB'],
                'QtGui'      : ['QT_GUI_LIB'],
                'QtNetwork'  : ['QT_NETWORK_LIB'],
                'QtCore'     : ['QT_CORE_LIB'],
                'QtWidgets'  : ['QT_WIDGETS_LIB'],
            }

            module_defines = qt5_module_defines if qt5 else qt4_module_defines
            for module in qt_modules:
                build.env.AppendUnique(CPPDEFINES=module_defines.get(module, []))

            if qt5:
                build.env["QT5_MOCCPPPATH"] = build.env["CPPPATH"]
            else:
                build.env["QT4_MOCCPPPATH"] = build.env["CPPPATH"]
        elif build.platform_is_windows:
            # This automatically converts QtCore to QtCore[45][d] where
            # appropriate.
            if qt5:
                build.env.EnableQt5Modules(qt_modules,
                                           staticdeps=build.static_qt,
                                           debug=build.build_is_debug)
            else:
                build.env.EnableQt4Modules(qt_modules,
                                           staticdeps=build.static_qt,
                                           debug=build.build_is_debug)

            if build.static_qt:
                # Pulled from qt-4.8.2-source\mkspecs\win32-msvc2010\qmake.conf
                # QtCore
                build.env.Append(LIBS = 'kernel32')
                build.env.Append(LIBS = 'user32') # QtGui, QtOpenGL, libHSS1394
                build.env.Append(LIBS = 'shell32')
                build.env.Append(LIBS = 'uuid')
                build.env.Append(LIBS = 'ole32') # QtGui,
                build.env.Append(LIBS = 'advapi32') # QtGui, portaudio, portmidi
                build.env.Append(LIBS = 'ws2_32')   # QtGui, QtNetwork, libshout
                # QtGui
                build.env.Append(LIBS = 'gdi32') #QtOpenGL, libshout
                build.env.Append(LIBS = 'comdlg32')
                build.env.Append(LIBS = 'oleaut32')
                build.env.Append(LIBS = 'imm32')
                build.env.Append(LIBS = 'winmm')
                build.env.Append(LIBS = 'winspool')
                # QtOpenGL
                build.env.Append(LIBS = 'glu32')
                build.env.Append(LIBS = 'opengl32')

                # QtNetwork openssl-linked
                build.env.Append(LIBS = 'crypt32')

                # New libraries required by Qt5.
                if qt5:
                    build.env.Append(LIBS = 'dwmapi')  # qtwindows
                    build.env.Append(LIBS = 'iphlpapi')  # qt5network
                    build.env.Append(LIBS = 'libEGL')  # qt5opengl
                    build.env.Append(LIBS = 'libGLESv2')  # qt5opengl
                    build.env.Append(LIBS = 'mpr')  # qt5core
                    build.env.Append(LIBS = 'netapi32')  # qt5core
                    build.env.Append(LIBS = 'userenv')  # qt5core
                    build.env.Append(LIBS = 'uxtheme')  # ?
                    build.env.Append(LIBS = 'version')  # ?

                    build.env.Append(LIBS = 'qtfreetype')
                    build.env.Append(LIBS = 'qtharfbuzz')
                    build.env.Append(LIBS = 'qtlibpng')
                    build.env.Append(LIBS = 'qtpcre2')

                # NOTE(rryan): If you are adding a plugin here, you must also
                # update src/mixxxapplication.cpp to define a Q_IMPORT_PLUGIN
                # for it. Not all imageformats plugins are built as .libs when
                # building Qt statically on Windows. Check the build environment
                # to see exactly what's available as a standalone .lib vs linked
                # into Qt .libs by default.

                # iconengines plugins
                build.env.Append(LIBPATH=[
                    os.path.join(build.env['QTDIR'],'plugins/iconengines')])
                build.env.Append(LIBS = 'qsvgicon')

                # imageformats plugins
                build.env.Append(LIBPATH=[
                    os.path.join(build.env['QTDIR'],'plugins/imageformats')])
                build.env.Append(LIBS = 'qico')
                build.env.Append(LIBS = 'qsvg')
                build.env.Append(LIBS = 'qtga')
                # not needed with Qt4
                if qt5:
                    build.env.Append(LIBS = 'qgif')
                    build.env.Append(LIBS = 'qjpeg')

                # accessibility plugins (gone in Qt5)
                if not qt5:
                    build.env.Append(LIBPATH=[
                        os.path.join(build.env['QTDIR'],'plugins/accessible')])
                    build.env.Append(LIBS = 'qtaccessiblewidgets')

                # platform plugins (new in Qt5 for Windows)
                if qt5:
                    build.env.Append(LIBPATH=[
                        os.path.join(build.env['QTDIR'],'plugins/platforms')])
                    build.env.Append(LIBS = 'qwindows')

                # styles (new in Qt5 for Windows)
                if qt5:
                    build.env.Append(LIBPATH=[
                        os.path.join(build.env['QTDIR'],'plugins/styles')])
                    build.env.Append(LIBS = 'qwindowsvistastyle')

                # sqldrivers (new in Qt5? or did we just start enabling them)
                if qt5:
                    build.env.Append(LIBPATH=[
                        os.path.join(build.env['QTDIR'],'plugins/sqldrivers')])
                    build.env.Append(LIBS = 'qsqlite')



        # Set the rpath for linux/bsd/osx.
        # This is not supported on OS X before the 10.5 SDK.
        using_104_sdk = (str(build.env["CCFLAGS"]).find("10.4") >= 0)
        compiling_on_104 = False
        if build.platform_is_osx:
            compiling_on_104 = (
                os.popen('sw_vers').readlines()[1].find('10.4') >= 0)
        if not build.platform_is_windows and not (using_104_sdk or compiling_on_104):
            qtdir = build.env['QTDIR']
            framework_path = Qt.find_framework_libdir(qtdir, qt5)
            if os.path.isdir(framework_path):
                build.env.Append(LINKFLAGS="-L" + framework_path)

        # Mixxx requires C++11 support. Windows enables C++11 features by
        # default but Clang/GCC require a flag.
        if not build.platform_is_windows:
            build.env.Append(CXXFLAGS='-std=c++11')


class TestHeaders(Dependence):
    def configure(self, build, conf):
        build.env.Append(CPPPATH="#lib/gtest-1.7.0/include")

class FidLib(Dependence):
    def sources(self, build):
        symbol = None
        if build.platform_is_windows:
            if build.toolchain_is_msvs:
                symbol = 'T_MSVC'
            elif build.crosscompile:
                # Not sure why, but fidlib won't build with mingw32msvc and
                # T_MINGW
                symbol = 'T_LINUX'
            elif build.toolchain_is_gnu:
                symbol = 'T_MINGW'
        else:
            symbol = 'T_LINUX'

        return [build.env.StaticObject('#lib/fidlib/fidlib.c',
                                       CPPDEFINES=symbol)]

    def configure(self, build, conf):
        build.env.Append(CPPPATH='#lib/fidlib/')


class ReplayGain(Dependence):

    def sources(self, build):
        return ["#lib/replaygain/replaygain.cpp"]

    def configure(self, build, conf):
        build.env.Append(CPPPATH="#lib/replaygain")


class Ebur128Mit(Dependence):
    INTERNAL_PATH = '#lib/libebur128'
    INTERNAL_LINK = False

    def sources(self, build):
        if self.INTERNAL_LINK:
            return ['%s/ebur128/ebur128.c' % self.INTERNAL_PATH]

    def configure(self, build, conf, env=None):
        if env is None:
            env = build.env
        if not conf.CheckLib(['ebur128', 'libebur128']):
            self.INTERNAL_LINK = True;
            env.Append(CPPPATH=['%s/ebur128' % self.INTERNAL_PATH])
            if not conf.CheckHeader('sys/queue.h'):
                env.Append(CPPPATH=['%s/ebur128/queue' % self.INTERNAL_PATH])


class SoundTouch(Dependence):
    SOUNDTOUCH_INTERNAL_PATH = '#lib/soundtouch'
    INTERNAL_LINK = True

    def sources(self, build):
        if self.INTERNAL_LINK:
            return ['engine/enginebufferscalest.cpp',
                    '%s/AAFilter.cpp' % self.SOUNDTOUCH_INTERNAL_PATH,
                    '%s/BPMDetect.cpp' % self.SOUNDTOUCH_INTERNAL_PATH,
                    '%s/FIFOSampleBuffer.cpp' % self.SOUNDTOUCH_INTERNAL_PATH,
                    '%s/FIRFilter.cpp' % self.SOUNDTOUCH_INTERNAL_PATH,
                    '%s/InterpolateCubic.cpp' % self.SOUNDTOUCH_INTERNAL_PATH,
                    '%s/InterpolateLinear.cpp' % self.SOUNDTOUCH_INTERNAL_PATH,
                    '%s/InterpolateShannon.cpp' % self.SOUNDTOUCH_INTERNAL_PATH,
                    '%s/PeakFinder.cpp' % self.SOUNDTOUCH_INTERNAL_PATH,
                    '%s/RateTransposer.cpp' % self.SOUNDTOUCH_INTERNAL_PATH,
                    '%s/SoundTouch.cpp' % self.SOUNDTOUCH_INTERNAL_PATH,
                    '%s/TDStretch.cpp' % self.SOUNDTOUCH_INTERNAL_PATH,
                    # SoundTouch CPU optimizations are only for x86
                    # architectures. SoundTouch automatically ignores these files
                    # when it is not being built for an architecture that supports
                    # them.
                    '%s/cpu_detect_x86.cpp' % self.SOUNDTOUCH_INTERNAL_PATH,
                    '%s/mmx_optimized.cpp' % self.SOUNDTOUCH_INTERNAL_PATH,
                    '%s/sse_optimized.cpp' % self.SOUNDTOUCH_INTERNAL_PATH]
        else:
            return ['engine/enginebufferscalest.cpp']

    def configure(self, build, conf, env=None):
        if env is None:
            env = build.env

        if build.platform_is_linux:
            # Try using system lib
            if conf.CheckForPKG('soundtouch', '2.0.0'):
                # System Lib found
                build.env.ParseConfig('pkg-config soundtouch --silence-errors \
                                      --cflags --libs')
                self.INTERNAL_LINK = False

        if self.INTERNAL_LINK:
            env.Append(CPPPATH=[self.SOUNDTOUCH_INTERNAL_PATH])

            # Prevents circular import.
            from .features import Optimize

            # If we do not want optimizations then disable them.
            optimize = (build.flags['optimize'] if 'optimize' in build.flags
                        else Optimize.get_optimization_level(build))
            if optimize == Optimize.LEVEL_OFF:
                env.Append(CPPDEFINES='SOUNDTOUCH_DISABLE_X86_OPTIMIZATIONS')

class RubberBand(Dependence):
    def sources(self, build):
        sources = ['engine/enginebufferscalerubberband.cpp', ]
        return sources

    def configure(self, build, conf, env=None):
        if env is None:
            env = build.env
        if not conf.CheckLib(['rubberband', 'librubberband']):
            raise Exception(
                "Could not find librubberband or its development headers.")


class TagLib(Dependence):
    def configure(self, build, conf):
        libs = ['tag']
        if not conf.CheckLib(libs):
            raise Exception(
                "Could not find libtag or its development headers.")

        # Karmic seems to have an issue with mp4tag.h where they don't include
        # the files correctly. Adding this folder to the include path should fix
        # it, though might cause issues. This is safe to remove once we
        # deprecate Karmic support. rryan 2/2011
        build.env.Append(CPPPATH='/usr/include/taglib/')

        if build.platform_is_windows and build.static_dependencies:
            build.env.Append(CPPDEFINES='TAGLIB_STATIC')


class Chromaprint(Dependence):
    def configure(self, build, conf):
        if not conf.CheckLib(['chromaprint', 'libchromaprint', 'chromaprint_p', 'libchromaprint_p']):
            raise Exception(
                "Could not find libchromaprint or its development headers.")
        if build.platform_is_windows and build.static_dependencies:
            build.env.Append(CPPDEFINES='CHROMAPRINT_NODLL')

            # On Windows, we link chromaprint with FFTW3.
            if not conf.CheckLib(['fftw', 'libfftw', 'fftw3', 'libfftw3', 'libfftw-3.3']):
                raise Exception(
                    "Could not find fftw3 or its development headers.")


class ProtoBuf(Dependence):
    def configure(self, build, conf):
        libs = ['libprotobuf-lite', 'protobuf-lite', 'libprotobuf', 'protobuf']
        if build.platform_is_windows:
            if not build.static_dependencies:
                build.env.Append(CPPDEFINES='PROTOBUF_USE_DLLS')
        # SCons is supposed to check this for us by calling 'exists' in build/protoc.py.
        protoc_binary = build.env['PROTOC']
        if build.env.WhereIs(protoc_binary) is None:
            raise Exception("Can't locate '%s' the protobuf compiler." % protoc_binary)
        if not conf.CheckLib(libs):
            raise Exception(
                "Could not find libprotobuf or its development headers.")

class FpClassify(Dependence):

    def enabled(self, build):
        return build.toolchain_is_gnu

    # This is a wrapper around the fpclassify function that prevents inlining
    # It is compiled without optimization and allows to use these function
    # from -ffast-math optimized objects
    def sources(self, build):
        # add this file without fast-math flag
        env = build.env.Clone()
        if '-ffast-math' in env['CCFLAGS']:
                env['CCFLAGS'].remove('-ffast-math')
        return env.Object('util/fpclassify.cpp')

class QtScriptByteArray(Dependence):
    def configure(self, build, conf):
        build.env.Append(CPPPATH='#lib/qtscript-bytearray')

    def sources(self, build):
        return ['#lib/qtscript-bytearray/bytearrayclass.cpp',
                '#lib/qtscript-bytearray/bytearrayprototype.cpp']

class PortAudioRingBuffer(Dependence):
    def configure(self, build, conf):
        build.env.Append(CPPPATH='#lib/portaudio')

    def sources(self, build):
        return ['#lib/portaudio/pa_ringbuffer.c']

class Reverb(Dependence):
    def configure(self, build, conf):
        build.env.Append(CPPPATH='#lib/reverb')

    def sources(self, build):
        return ['#lib/reverb/Reverb.cc']

class QtKeychain(Dependence):
    def configure(self, build, conf):
        lib = 'qt5keychain' if Qt.qt5_enabled(build) else 'qtkeychain'
        if not conf.CheckLib(lib):
            raise Exception("Could not find %s." % lib)

class LAME(Dependence):
    def configure(self, build, conf):
        if not conf.CheckLib(['libmp3lame', 'libmp3lame-static']):
            raise Exception("Could not find libmp3lame.")

class MixxxCore(Feature):

    def description(self):
        return "Mixxx Core Features"

    def enabled(self, build):
        return True

    def sources(self, build):
        sources = ["control/control.cpp",
                   "control/controlaudiotaperpot.cpp",
                   "control/controlbehavior.cpp",
                   "control/controleffectknob.cpp",
                   "control/controlindicator.cpp",
                   "control/controllinpotmeter.cpp",
                   "control/controllogpotmeter.cpp",
                   "control/controlmodel.cpp",
                   "control/controlobject.cpp",
                   "control/controlobjectscript.cpp",
                   "control/controlpotmeter.cpp",
                   "control/controlproxy.cpp",
                   "control/controlpushbutton.cpp",
                   "control/controlttrotary.cpp",
                   "control/controlencoder.cpp",

                   "controllers/dlgcontrollerlearning.cpp",
                   "controllers/dlgprefcontroller.cpp",
                   "controllers/dlgprefcontrollers.cpp",
                   "dialog/dlgabout.cpp",
                   "dialog/dlgdevelopertools.cpp",

                   "preferences/configobject.cpp",
                   "preferences/dialog/dlgprefautodj.cpp",
                   "preferences/dialog/dlgprefdeck.cpp",
                   "preferences/dialog/dlgprefcrossfader.cpp",
                   "preferences/dialog/dlgprefeffects.cpp",
                   "preferences/dialog/dlgprefeq.cpp",
                   "preferences/dialog/dlgpreferences.cpp",
                   "preferences/dialog/dlgprefinterface.cpp",
                   "preferences/dialog/dlgpreflibrary.cpp",
                   "preferences/dialog/dlgprefnovinyl.cpp",
                   "preferences/dialog/dlgprefrecord.cpp",
                   "preferences/dialog/dlgprefreplaygain.cpp",
                   "preferences/dialog/dlgprefsound.cpp",
                   "preferences/dialog/dlgprefsounditem.cpp",
                   "preferences/dialog/dlgprefwaveform.cpp",
                   "preferences/settingsmanager.cpp",
                   "preferences/replaygainsettings.cpp",
                   "preferences/broadcastsettings.cpp",
                   "preferences/broadcastsettings_legacy.cpp",
                   "preferences/broadcastsettingsmodel.cpp",
                   "preferences/effectsettingsmodel.cpp",
                   "preferences/broadcastprofile.cpp",
                   "preferences/upgrade.cpp",
                   "preferences/dlgpreferencepage.cpp",

                   "effects/effectmanifest.cpp",
                   "effects/effectmanifestparameter.cpp",

                   "effects/effectchain.cpp",
                   "effects/effect.cpp",
                   "effects/effectparameter.cpp",

                   "effects/effectrack.cpp",
                   "effects/effectchainslot.cpp",
                   "effects/effectslot.cpp",
                   "effects/effectparameterslotbase.cpp",
                   "effects/effectparameterslot.cpp",
                   "effects/effectbuttonparameterslot.cpp",
                   "effects/effectsmanager.cpp",
                   "effects/effectchainmanager.cpp",
                   "effects/effectsbackend.cpp",

                   "effects/builtin/builtinbackend.cpp",
                   "effects/builtin/bitcrushereffect.cpp",
                   "effects/builtin/balanceeffect.cpp",
                   "effects/builtin/linkwitzriley8eqeffect.cpp",
                   "effects/builtin/bessel4lvmixeqeffect.cpp",
                   "effects/builtin/bessel8lvmixeqeffect.cpp",
                   "effects/builtin/threebandbiquadeqeffect.cpp",
                   "effects/builtin/biquadfullkilleqeffect.cpp",
                   "effects/builtin/loudnesscontoureffect.cpp",
                   "effects/builtin/graphiceqeffect.cpp",
                   "effects/builtin/parametriceqeffect.cpp",
                   "effects/builtin/flangereffect.cpp",
                   "effects/builtin/filtereffect.cpp",
                   "effects/builtin/moogladder4filtereffect.cpp",
                   "effects/builtin/reverbeffect.cpp",
                   "effects/builtin/echoeffect.cpp",
                   "effects/builtin/autopaneffect.cpp",
                   "effects/builtin/phasereffect.cpp",
                   "effects/builtin/metronomeeffect.cpp",
                   "effects/builtin/tremoloeffect.cpp",

                   "engine/effects/engineeffectsmanager.cpp",
                   "engine/effects/engineeffectrack.cpp",
                   "engine/effects/engineeffectchain.cpp",
                   "engine/effects/engineeffect.cpp",

                   "engine/sync/basesyncablelistener.cpp",
                   "engine/sync/enginesync.cpp",
                   "engine/sync/synccontrol.cpp",
                   "engine/sync/internalclock.cpp",

                   "engine/engineworker.cpp",
                   "engine/engineworkerscheduler.cpp",
                   "engine/enginebuffer.cpp",
                   "engine/enginebufferscale.cpp",
                   "engine/enginebufferscalelinear.cpp",
                   "engine/enginefilterbiquad1.cpp",
                   "engine/enginefiltermoogladder4.cpp",
                   "engine/enginefilterbessel4.cpp",
                   "engine/enginefilterbessel8.cpp",
                   "engine/enginefilterbutterworth4.cpp",
                   "engine/enginefilterbutterworth8.cpp",
                   "engine/enginefilterlinkwitzriley2.cpp",
                   "engine/enginefilterlinkwitzriley4.cpp",
                   "engine/enginefilterlinkwitzriley8.cpp",
                   "engine/enginefilter.cpp",
                   "engine/engineobject.cpp",
                   "engine/enginepregain.cpp",
                   "engine/enginechannel.cpp",
                   "engine/enginemaster.cpp",
                   "engine/enginedelay.cpp",
                   "engine/enginevumeter.cpp",
                   "engine/enginesidechaincompressor.cpp",
                   "engine/sidechain/enginesidechain.cpp",
                   "engine/sidechain/networkoutputstreamworker.cpp",
                   "engine/sidechain/networkinputstreamworker.cpp",
                   "engine/enginexfader.cpp",
                   "engine/enginemicrophone.cpp",
                   "engine/enginedeck.cpp",
                   "engine/engineaux.cpp",
                   "engine/channelmixer_autogen.cpp",

                   "engine/enginecontrol.cpp",
                   "engine/ratecontrol.cpp",
                   "engine/positionscratchcontroller.cpp",
                   "engine/loopingcontrol.cpp",
                   "engine/bpmcontrol.cpp",
                   "engine/keycontrol.cpp",
                   "engine/cuecontrol.cpp",
                   "engine/quantizecontrol.cpp",
                   "engine/clockcontrol.cpp",
                   "engine/readaheadmanager.cpp",
                   "engine/enginetalkoverducking.cpp",
                   "engine/cachingreader.cpp",
                   "engine/cachingreaderchunk.cpp",
                   "engine/cachingreaderworker.cpp",

                   "analyzer/analyzerqueue.cpp",
                   "analyzer/analyzerwaveform.cpp",
                   "analyzer/analyzergain.cpp",
                   "analyzer/analyzerebur128.cpp",

                   "controllers/controller.cpp",
                   "controllers/controllerdebug.cpp",
                   "controllers/controllerengine.cpp",
                   "controllers/controllerenumerator.cpp",
                   "controllers/controllerlearningeventfilter.cpp",
                   "controllers/controllermanager.cpp",
                   "controllers/controllerpresetfilehandler.cpp",
                   "controllers/controllerpresetinfo.cpp",
                   "controllers/controllerpresetinfoenumerator.cpp",
                   "controllers/controlpickermenu.cpp",
                   "controllers/controllermappingtablemodel.cpp",
                   "controllers/controllerinputmappingtablemodel.cpp",
                   "controllers/controlleroutputmappingtablemodel.cpp",
                   "controllers/delegates/controldelegate.cpp",
                   "controllers/delegates/midichanneldelegate.cpp",
                   "controllers/delegates/midiopcodedelegate.cpp",
                   "controllers/delegates/midibytedelegate.cpp",
                   "controllers/delegates/midioptionsdelegate.cpp",
                   "controllers/learningutils.cpp",
                   "controllers/midi/midimessage.cpp",
                   "controllers/midi/midiutils.cpp",
                   "controllers/midi/midicontroller.cpp",
                   "controllers/midi/midicontrollerpresetfilehandler.cpp",
                   "controllers/midi/midienumerator.cpp",
                   "controllers/midi/midioutputhandler.cpp",
                   "controllers/softtakeover.cpp",
                   "controllers/keyboard/keyboardeventfilter.cpp",

                   "main.cpp",
                   "mixxx.cpp",
                   "mixxxapplication.cpp",
                   "errordialoghandler.cpp",

                   "sources/audiosource.cpp",
                   "sources/audiosourcestereoproxy.cpp",
                   "sources/metadatasourcetaglib.cpp",
                   "sources/soundsource.cpp",
                   "sources/soundsourceproviderregistry.cpp",
                   "sources/soundsourceproxy.cpp",

                   "widget/controlwidgetconnection.cpp",
                   "widget/wbasewidget.cpp",
                   "widget/wwidget.cpp",
                   "widget/wwidgetgroup.cpp",
                   "widget/wwidgetstack.cpp",
                   "widget/wsizeawarestack.cpp",
                   "widget/wlabel.cpp",
                   "widget/wtracktext.cpp",
                   "widget/wnumber.cpp",
                   "widget/wbeatspinbox.cpp",
                   "widget/wnumberdb.cpp",
                   "widget/wnumberpos.cpp",
                   "widget/wnumberrate.cpp",
                   "widget/wknob.cpp",
                   "widget/wknobcomposed.cpp",
                   "widget/wdisplay.cpp",
                   "widget/wvumeter.cpp",
                   "widget/wpushbutton.cpp",
                   "widget/weffectpushbutton.cpp",
                   "widget/wslidercomposed.cpp",
                   "widget/wstatuslight.cpp",
                   "widget/woverview.cpp",
                   "widget/woverviewlmh.cpp",
                   "widget/woverviewhsv.cpp",
                   "widget/woverviewrgb.cpp",
                   "widget/wspinny.cpp",
                   "widget/wskincolor.cpp",
                   "widget/wsearchlineedit.cpp",
                   "widget/wpixmapstore.cpp",
                   "widget/paintable.cpp",
                   "widget/wimagestore.cpp",
                   "widget/hexspinbox.cpp",
                   "widget/wtrackproperty.cpp",
                   "widget/wstarrating.cpp",
                   "widget/weffectchain.cpp",
                   "widget/weffect.cpp",
                   "widget/weffectselector.cpp",
                   "widget/weffectparameter.cpp",
                   "widget/weffectparameterknob.cpp",
                   "widget/weffectparameterknobcomposed.cpp",
                   "widget/weffectbuttonparameter.cpp",
                   "widget/weffectparameterbase.cpp",
                   "widget/wtime.cpp",
                   "widget/wrecordingduration.cpp",
                   "widget/wkey.cpp",
                   "widget/wbattery.cpp",
                   "widget/wcombobox.cpp",
                   "widget/wsplitter.cpp",
                   "widget/wcoverart.cpp",
                   "widget/wcoverartlabel.cpp",
                   "widget/wcoverartmenu.cpp",
                   "widget/wsingletoncontainer.cpp",
                   "widget/wmainmenubar.cpp",

                   "musicbrainz/network.cpp",
                   "musicbrainz/tagfetcher.cpp",
                   "musicbrainz/gzip.cpp",
                   "musicbrainz/crc.c",
                   "musicbrainz/acoustidclient.cpp",
                   "musicbrainz/chromaprinter.cpp",
                   "musicbrainz/musicbrainzclient.cpp",

                   "widget/wtracktableview.cpp",
                   "widget/wtracktableviewheader.cpp",
                   "widget/wlibrarysidebar.cpp",
                   "widget/wlibrary.cpp",
                   "widget/wlibrarytableview.cpp",
                   "widget/wanalysislibrarytableview.cpp",
                   "widget/wlibrarytextbrowser.cpp",

                   "database/mixxxdb.cpp",
                   "database/schemamanager.cpp",

                   "library/trackcollection.cpp",
                   "library/basesqltablemodel.cpp",
                   "library/basetrackcache.cpp",
                   "library/columncache.cpp",
                   "library/librarytablemodel.cpp",
                   "library/searchquery.cpp",
                   "library/searchqueryparser.cpp",
                   "library/analysislibrarytablemodel.cpp",
                   "library/missingtablemodel.cpp",
                   "library/hiddentablemodel.cpp",
                   "library/proxytrackmodel.cpp",
                   "library/coverart.cpp",
                   "library/coverartcache.cpp",
                   "library/coverartutils.cpp",

                   "library/crate/cratestorage.cpp",
                   "library/crate/cratefeature.cpp",
                   "library/crate/cratefeaturehelper.cpp",
                   "library/crate/cratetablemodel.cpp",

                   "library/playlisttablemodel.cpp",
                   "library/libraryfeature.cpp",
                   "library/analysisfeature.cpp",
                   "library/autodj/autodjfeature.cpp",
                   "library/autodj/autodjprocessor.cpp",
                   "library/dao/directorydao.cpp",
                   "library/mixxxlibraryfeature.cpp",
                   "library/baseplaylistfeature.cpp",
                   "library/playlistfeature.cpp",
                   "library/setlogfeature.cpp",
                   "library/autodj/dlgautodj.cpp",
                   "library/dlganalysis.cpp",
                   "library/dlgcoverartfullsize.cpp",
                   "library/dlghidden.cpp",
                   "library/dlgmissing.cpp",
                   "library/dlgtagfetcher.cpp",
                   "library/dlgtrackinfo.cpp",
                   "library/dlgtrackmetadataexport.cpp",

                   "library/browse/browsetablemodel.cpp",
                   "library/browse/browsethread.cpp",
                   "library/browse/browsefeature.cpp",
                   "library/browse/foldertreemodel.cpp",

                   "library/export/trackexportdlg.cpp",
                   "library/export/trackexportwizard.cpp",
                   "library/export/trackexportworker.cpp",

                   "library/recording/recordingfeature.cpp",
                   "library/recording/dlgrecording.cpp",
                   "recording/recordingmanager.cpp",
                   "engine/sidechain/enginerecord.cpp",

                   # External Library Features
                   "library/baseexternallibraryfeature.cpp",
                   "library/baseexternaltrackmodel.cpp",
                   "library/baseexternalplaylistmodel.cpp",
                   "library/rhythmbox/rhythmboxfeature.cpp",

                   "library/banshee/bansheefeature.cpp",
                   "library/banshee/bansheeplaylistmodel.cpp",
                   "library/banshee/bansheedbconnection.cpp",

                   "library/itunes/itunesfeature.cpp",
                   "library/traktor/traktorfeature.cpp",

                   "library/sidebarmodel.cpp",
                   "library/library.cpp",

                   "library/scanner/libraryscanner.cpp",
                   "library/scanner/libraryscannerdlg.cpp",
                   "library/scanner/scannertask.cpp",
                   "library/scanner/importfilestask.cpp",
                   "library/scanner/recursivescandirectorytask.cpp",

                   "library/dao/cuedao.cpp",
                   "library/dao/cue.cpp",
                   "library/dao/trackdao.cpp",
                   "library/dao/playlistdao.cpp",
                   "library/dao/libraryhashdao.cpp",
                   "library/dao/settingsdao.cpp",
                   "library/dao/analysisdao.cpp",
                   "library/dao/autodjcratesdao.cpp",

                   "library/librarycontrol.cpp",
                   "library/songdownloader.cpp",
                   "library/starrating.cpp",
                   "library/stardelegate.cpp",
                   "library/stareditor.cpp",
                   "library/bpmdelegate.cpp",
                   "library/previewbuttondelegate.cpp",
                   "library/coverartdelegate.cpp",
				   "library/tableitemdelegate.cpp",

                   "library/treeitemmodel.cpp",
                   "library/treeitem.cpp",

                   "library/parser.cpp",
                   "library/parserpls.cpp",
                   "library/parserm3u.cpp",
                   "library/parsercsv.cpp",

                   "widget/wwaveformviewer.cpp",

                   "waveform/sharedglcontext.cpp",
                   "waveform/waveform.cpp",
                   "waveform/waveformfactory.cpp",
                   "waveform/waveformwidgetfactory.cpp",
                   "waveform/vsyncthread.cpp",
                   "waveform/guitick.cpp",
                   "waveform/visualplayposition.cpp",
                   "waveform/renderers/waveformwidgetrenderer.cpp",
                   "waveform/renderers/waveformrendererabstract.cpp",
                   "waveform/renderers/waveformrenderbackground.cpp",
                   "waveform/renderers/waveformrendermark.cpp",
                   "waveform/renderers/waveformrendermarkrange.cpp",
                   "waveform/renderers/waveformrenderbeat.cpp",
                   "waveform/renderers/waveformrendererendoftrack.cpp",
                   "waveform/renderers/waveformrendererpreroll.cpp",

                   "waveform/renderers/waveformrendererfilteredsignal.cpp",
                   "waveform/renderers/waveformrendererhsv.cpp",
                   "waveform/renderers/waveformrendererrgb.cpp",
                   "waveform/renderers/qtwaveformrendererfilteredsignal.cpp",
                   "waveform/renderers/qtwaveformrenderersimplesignal.cpp",

                   "waveform/renderers/waveformsignalcolors.cpp",

                   "waveform/renderers/waveformrenderersignalbase.cpp",
                   "waveform/renderers/waveformmark.cpp",
                   "waveform/renderers/waveformmarkproperties.cpp",
                   "waveform/renderers/waveformmarkset.cpp",
                   "waveform/renderers/waveformmarkrange.cpp",
                   "waveform/renderers/glwaveformrenderersimplesignal.cpp",
                   "waveform/renderers/glwaveformrendererrgb.cpp",
                   "waveform/renderers/glwaveformrendererfilteredsignal.cpp",
                   "waveform/renderers/glslwaveformrenderersignal.cpp",
                   "waveform/renderers/glvsynctestrenderer.cpp",

                   "waveform/widgets/waveformwidgetabstract.cpp",
                   "waveform/widgets/emptywaveformwidget.cpp",
                   "waveform/widgets/softwarewaveformwidget.cpp",
                   "waveform/widgets/hsvwaveformwidget.cpp",
                   "waveform/widgets/rgbwaveformwidget.cpp",
                   "waveform/widgets/qtwaveformwidget.cpp",
                   "waveform/widgets/qtsimplewaveformwidget.cpp",
                   "waveform/widgets/glwaveformwidget.cpp",
                   "waveform/widgets/glsimplewaveformwidget.cpp",
                   "waveform/widgets/glvsynctestwidget.cpp",

                   "waveform/widgets/glslwaveformwidget.cpp",

                   "waveform/widgets/glrgbwaveformwidget.cpp",

                   "skin/imginvert.cpp",
                   "skin/imgloader.cpp",
                   "skin/imgcolor.cpp",
                   "skin/skinloader.cpp",
                   "skin/legacyskinparser.cpp",
                   "skin/colorschemeparser.cpp",
                   "skin/tooltips.cpp",
                   "skin/skincontext.cpp",
                   "skin/svgparser.cpp",
                   "skin/pixmapsource.cpp",
                   "skin/launchimage.cpp",

                   "track/beatfactory.cpp",
                   "track/beatgrid.cpp",
                   "track/beatmap.cpp",
                   "track/beatutils.cpp",
                   "track/beats.cpp",
                   "track/bpm.cpp",
                   "track/keyfactory.cpp",
                   "track/keys.cpp",
                   "track/keyutils.cpp",
                   "track/playcounter.cpp",
                   "track/replaygain.cpp",
                   "track/track.cpp",
                   "track/globaltrackcache.cpp",
                   "track/trackmetadata.cpp",
                   "track/trackmetadatataglib.cpp",
                   "track/tracknumbers.cpp",
                   "track/albuminfo.cpp",
                   "track/trackinfo.cpp",
                   "track/trackrecord.cpp",
                   "track/trackref.cpp",

                   "mixer/auxiliary.cpp",
                   "mixer/baseplayer.cpp",
                   "mixer/basetrackplayer.cpp",
                   "mixer/deck.cpp",
                   "mixer/microphone.cpp",
                   "mixer/playerinfo.cpp",
                   "mixer/playermanager.cpp",
                   "mixer/previewdeck.cpp",
                   "mixer/sampler.cpp",
                   "mixer/samplerbank.cpp",

                   "soundio/sounddevice.cpp",
                   "soundio/sounddevicenetwork.cpp",
                   "engine/sidechain/enginenetworkstream.cpp",
                   "soundio/soundmanager.cpp",
                   "soundio/soundmanagerconfig.cpp",
                   "soundio/soundmanagerutil.cpp",

                   "encoder/encoder.cpp",
                   "encoder/encodermp3.cpp",
                   "encoder/encodervorbis.cpp",
                   "encoder/encoderwave.cpp",
                   "encoder/encodersndfileflac.cpp",
                   "encoder/encodermp3settings.cpp",
                   "encoder/encodervorbissettings.cpp",
                   "encoder/encoderwavesettings.cpp",
                   "encoder/encoderflacsettings.cpp",
                   "encoder/encoderbroadcastsettings.cpp",

                   "util/sleepableqthread.cpp",
                   "util/statsmanager.cpp",
                   "util/stat.cpp",
                   "util/statmodel.cpp",
                   "util/duration.cpp",
                   "util/time.cpp",
                   "util/timer.cpp",
                   "util/performancetimer.cpp",
                   "util/threadcputimer.cpp",
                   "util/version.cpp",
                   "util/rlimit.cpp",
                   "util/battery/battery.cpp",
                   "util/valuetransformer.cpp",
                   "util/sandbox.cpp",
                   "util/file.cpp",
                   "util/mac.cpp",
                   "util/task.cpp",
                   "util/experiment.cpp",
                   "util/xml.cpp",
                   "util/tapfilter.cpp",
                   "util/movinginterquartilemean.cpp",
                   "util/console.cpp",
                   "util/db/dbconnection.cpp",
                   "util/db/dbconnectionpool.cpp",
                   "util/db/dbconnectionpooler.cpp",
                   "util/db/dbconnectionpooled.cpp",
                   "util/db/dbid.cpp",
                   "util/db/fwdsqlquery.cpp",
                   "util/db/fwdsqlqueryselectresult.cpp",
                   "util/db/sqllikewildcardescaper.cpp",
                   "util/db/sqlqueryfinisher.cpp",
                   "util/db/sqlstringformatter.cpp",
                   "util/db/sqltransaction.cpp",
                   "util/sample.cpp",
                   "util/samplebuffer.cpp",
                   "util/readaheadsamplebuffer.cpp",
                   "util/rotary.cpp",
                   "util/logger.cpp",
                   "util/logging.cpp",
                   "util/cmdlineargs.cpp",
                   "util/audiosignal.cpp",
                   "util/widgethider.cpp",
                   "util/autohidpi.cpp",
                   "util/screensaver.cpp",
                   "util/indexrange.cpp",

                   '#res/mixxx.qrc'
                   ]

        proto_args = {
            'PROTOCPROTOPATH': ['src'],
            'PROTOCPYTHONOUTDIR': '',  # set to None to not generate python
            'PROTOCOUTDIR': build.build_dir,
            'PROTOCCPPOUTFLAGS': '',
            #'PROTOCCPPOUTFLAGS': "dllexport_decl=PROTOCONFIG_EXPORT:"
        }
        proto_sources = SCons.Glob('proto/*.proto')
        proto_objects = [build.env.Protoc([], proto_source, **proto_args)[0]
                         for proto_source in proto_sources]
        sources.extend(proto_objects)

        # Uic these guys (they're moc'd automatically after this) - Generates
        # the code for the QT UI forms.
        ui_files = [
            'controllers/dlgcontrollerlearning.ui',
            'controllers/dlgprefcontrollerdlg.ui',
            'controllers/dlgprefcontrollersdlg.ui',
            'dialog/dlgaboutdlg.ui',
            'dialog/dlgdevelopertoolsdlg.ui',
            'library/autodj/dlgautodj.ui',
            'library/dlganalysis.ui',
            'library/dlgcoverartfullsize.ui',
            'library/dlghidden.ui',
            'library/dlgmissing.ui',
            'library/dlgtagfetcher.ui',
            'library/dlgtrackinfo.ui',
            'library/export/dlgtrackexport.ui',
            'library/recording/dlgrecording.ui',
            'preferences/dialog/dlgprefautodjdlg.ui',
            'preferences/dialog/dlgprefbeatsdlg.ui',
            'preferences/dialog/dlgprefdeckdlg.ui',
            'preferences/dialog/dlgprefcrossfaderdlg.ui',
            'preferences/dialog/dlgpreflv2dlg.ui',
            'preferences/dialog/dlgprefeffectsdlg.ui',
            'preferences/dialog/dlgprefeqdlg.ui',
            'preferences/dialog/dlgpreferencesdlg.ui',
            'preferences/dialog/dlgprefinterfacedlg.ui',
            'preferences/dialog/dlgprefkeydlg.ui',
            'preferences/dialog/dlgpreflibrarydlg.ui',
            'preferences/dialog/dlgprefnovinyldlg.ui',
            'preferences/dialog/dlgprefrecorddlg.ui',
            'preferences/dialog/dlgprefreplaygaindlg.ui',
            'preferences/dialog/dlgprefsounddlg.ui',
            'preferences/dialog/dlgprefsounditem.ui',
            'preferences/dialog/dlgprefvinyldlg.ui',
            'preferences/dialog/dlgprefwaveformdlg.ui',
        ]
        map(Qt.uic(build), ui_files)

        if build.platform_is_windows:
            # Add Windows resource file with icons and such
            # force manifest file creation, apparently not necessary for all
            # people but necessary for this committers handicapped windows
            # installation -- bkgood
            if build.toolchain_is_msvs:
                build.env.Append(LINKFLAGS="/MANIFEST")
        elif build.platform_is_osx:
            # Need extra room for code signing (App Store)
            build.env.Append(LINKFLAGS="-Wl,-headerpad,ffff")
            build.env.Append(LINKFLAGS="-Wl,-headerpad_max_install_names")

        return sources

    def configure(self, build, conf):
        # Evaluate this define. There are a lot of different things around the
        # codebase that use different defines. (AMD64, x86_64, x86, i386, i686,
        # EM64T). We need to unify them together.
        if not build.machine == 'alpha':
            build.env.Append(CPPDEFINES=build.machine)

        # TODO(rryan): Quick hack to get the build number in title bar. Clean up
        # later.
        if int(SCons.ARGUMENTS.get('build_number_in_title_bar', 0)):
            build.env.Append(CPPDEFINES='MIXXX_BUILD_NUMBER_IN_TITLE_BAR')

        if build.build_is_debug:
            build.env.Append(CPPDEFINES='MIXXX_BUILD_DEBUG')
        elif build.build_is_release:
            build.env.Append(CPPDEFINES='MIXXX_BUILD_RELEASE')
            # Disable assert.h assertions in release mode. Some libraries use
            # this as a signal for when to enable code that should be disabled
            # in release mode.
            build.env.Append(CPPDEFINES='NDEBUG')

            # In a release build we want to disable all Q_ASSERTs in Qt headers
            # that we include. We can't define QT_NO_DEBUG because that would
            # mean turning off QDebug output. qt_noop() is what Qt defined
            # Q_ASSERT to be when QT_NO_DEBUG is defined in Qt 5.9 and earlier.
            # Now it is defined as static_cast<void>(false&&(x)) to support use
            # in constexpr functions. We still use qt_noop on Windows since we
            # can't specify static_cast<void>(false&&(x)) in a commandline
            # macro definition, but it seems VS 2015 isn't bothered by the use
            # qt_noop here, so we can keep it.
            if build.platform_is_windows:
                build.env.Append(CPPDEFINES="'Q_ASSERT(x)=qt_noop()'")
            else:
                build.env.Append(CPPDEFINES="'Q_ASSERT(x)=static_cast<void>(false&&(x))'")

        if int(SCons.ARGUMENTS.get('debug_assertions_fatal', 0)):
            build.env.Append(CPPDEFINES='MIXXX_DEBUG_ASSERTIONS_FATAL')

        if build.toolchain_is_gnu:
            # Default GNU Options
            build.env.Append(CCFLAGS='-pipe')
            build.env.Append(CCFLAGS='-Wall')
            if build.compiler_is_clang:
                # Quiet down Clang warnings about inconsistent use of override
                # keyword until Qt fixes qt_metacall.
                build.env.Append(CCFLAGS='-Wno-inconsistent-missing-override')

                # Do not warn about use of the deprecated 'register' keyword
                # since it produces noise from libraries we depend on using it.
                build.env.Append(CCFLAGS='-Wno-deprecated-register')

                # Warn about implicit fallthrough.
                build.env.Append(CCFLAGS='-Wimplicit-fallthrough')

                # Enable thread-safety analysis.
                # http://clang.llvm.org/docs/ThreadSafetyAnalysis.html
                build.env.Append(CCFLAGS='-Wthread-safety')
            build.env.Append(CCFLAGS='-Wextra')

            # Always generate debugging info.
            build.env.Append(CCFLAGS='-g')
        elif build.toolchain_is_msvs:
            # Validate the specified winlib directory exists
            mixxx_lib_path = build.winlib_path
            if not os.path.exists(mixxx_lib_path):
                raise Exception("Winlib path does not exist! Please specify your winlib directory"
                                "path by running 'scons winlib=[path]'")
                Script.Exit(1)

            # Set include and library paths to work with this
            build.env.Append(CPPPATH=[mixxx_lib_path,
                                      os.path.join(mixxx_lib_path, 'include')])
            build.env.Append(LIBPATH=[mixxx_lib_path, os.path.join(mixxx_lib_path, 'lib')])

            # Find executables (e.g. protoc) in the winlib path
            build.env.AppendENVPath('PATH', mixxx_lib_path)
            build.env.AppendENVPath('PATH', os.path.join(mixxx_lib_path, 'bin'))

            # Valid values of /MACHINE are: {ARM|EBC|X64|X86}
            # http://msdn.microsoft.com/en-us/library/5wy54dk2.aspx
            if build.architecture_is_x86:
                if build.machine_is_64bit:
                    build.env.Append(LINKFLAGS='/MACHINE:X64')
                else:
                    build.env.Append(LINKFLAGS='/MACHINE:X86')
            elif build.architecture_is_arm:
                build.env.Append(LINKFLAGS='/MACHINE:ARM')
            else:
                raise Exception('Invalid machine type for Windows build.')

            # Build with multiple processes. TODO(XXX) make this configurable.
            # http://msdn.microsoft.com/en-us/library/bb385193.aspx
            build.env.Append(CCFLAGS='/MP')

            # Generate debugging information for compilation units and
            # executables linked if we are creating a debug build or bundling
            # PDBs is enabled.  Having PDB files for our releases is helpful for
            # debugging, but increases link times and memory usage
            # significantly.
            if build.build_is_debug or build.bundle_pdbs:
                build.env.Append(LINKFLAGS='/DEBUG')
                build.env.Append(CCFLAGS='/Zi /Fd${TARGET}.pdb')

            if build.build_is_debug:
                # Important: We always build Mixxx with the Multi-Threaded DLL
                # runtime because Mixxx loads DLLs at runtime. Since this is a
                # debug build, use the debug version of the MD runtime.
                build.env.Append(CCFLAGS='/MDd')
            else:
                # Important: We always build Mixxx with the Multi-Threaded DLL
                # runtime because Mixxx loads DLLs at runtime.
                build.env.Append(CCFLAGS='/MD')

        if build.platform_is_windows:
            build.env.Append(CPPDEFINES='__WINDOWS__')
            # Restrict ATL to XP-compatible SDK functions.
            # TODO(rryan): Remove once we ditch XP support.
            build.env.Append(CPPDEFINES='_ATL_XP_TARGETING')
            build.env.Append(
                CPPDEFINES='_ATL_MIN_CRT')  # Helps prevent duplicate symbols
            # Need this on Windows until we have UTF16 support in Mixxx
            # use stl min max defines
            # http://connect.microsoft.com/VisualStudio/feedback/details/553420/std-cpp-max-and-std-cpp-min-not-available-in-visual-c-2010
            build.env.Append(CPPDEFINES='NOMINMAX')
            build.env.Append(CPPDEFINES='UNICODE')
            build.env.Append(
                CPPDEFINES='WIN%s' % build.bitwidth)  # WIN32 or WIN64
            # Tobias: Don't remove this line
            # I used the Windows API in foldertreemodel.cpp
            # to quickly test if a folder has subfolders
            build.env.Append(LIBS='shell32')

            # Causes the cmath headers to declare M_PI and friends.
            # http://msdn.microsoft.com/en-us/library/4hwaceh6.aspx
            # We could define this in our headers but then include order
            # matters since headers we don't control may include cmath first.
            build.env.Append(CPPDEFINES='_USE_MATH_DEFINES')

        elif build.platform_is_linux:
            build.env.Append(CPPDEFINES='__LINUX__')

            # Check for pkg-config >= 0.15.0
            if not conf.CheckForPKGConfig('0.15.0'):
                raise Exception('pkg-config >= 0.15.0 not found.')

            if not conf.CheckLib(['X11', 'libX11']):
                raise Exception(
                    "Could not find libX11 or its development headers.")

        elif build.platform_is_osx:
            # Stuff you may have compiled by hand
            if os.path.isdir('/usr/local/include'):
                build.env.Append(LIBPATH=['/usr/local/lib'])
                build.env.Append(CPPPATH=['/usr/local/include'])

        elif build.platform_is_bsd:
            build.env.Append(CPPDEFINES='__BSD__')
            build.env.Append(CPPPATH=['/usr/include',
                                      '/usr/local/include',
                                      '/usr/X11R6/include/'])
            build.env.Append(LIBPATH=['/usr/lib/',
                                      '/usr/local/lib',
                                      '/usr/X11R6/lib'])
            build.env.Append(LIBS='pthread')
            # why do we need to do this on OpenBSD and not on Linux?  if we
            # don't then CheckLib("vorbisfile") fails
            build.env.Append(LIBS=['ogg', 'vorbis'])

        # Define for things that would like to special case UNIX (Linux or BSD)
        if build.platform_is_bsd or build.platform_is_linux:
            build.env.Append(CPPDEFINES='__UNIX__')

        # Add the src/ directory to the include path
        build.env.Append(CPPPATH=['.'])

        # Set up flags for config/track listing files
        # SETTINGS_PATH not needed for windows and MacOSX because we now use QDesktopServices::storageLocation(QDesktopServices::DataLocation)
        if build.platform_is_linux or \
                build.platform_is_bsd:
            mixxx_files = [
                # TODO(XXX) Trailing slash not needed anymore as we switches from String::append
                # to QDir::filePath elsewhere in the code. This is candidate for removal.
                ('SETTINGS_PATH', '.mixxx/'),
                ('SETTINGS_FILE', 'mixxx.cfg')]
        elif build.platform_is_osx:
            mixxx_files = [
                ('SETTINGS_FILE', 'mixxx.cfg')]
        elif build.platform_is_windows:
            mixxx_files = [
                ('SETTINGS_FILE', 'mixxx.cfg')]

        # Escape the filenames so they don't end up getting screwed up in the
        # shell.
        mixxx_files = [(k, r'\"%s\"' % v) for k, v in mixxx_files]
        build.env.Append(CPPDEFINES=mixxx_files)

        # Say where to find resources on Unix. TODO(XXX) replace this with a
        # RESOURCE_PATH that covers Win and OSX too:
        if build.platform_is_linux or build.platform_is_bsd:
            prefix = SCons.ARGUMENTS.get('prefix', '/usr/local')
            share_path = os.path.join (prefix, build.env.get(
                'SHAREDIR', default='share'), 'mixxx')
            build.env.Append(
                CPPDEFINES=('UNIX_SHARE_PATH', r'\"%s\"' % share_path))
            lib_path = os.path.join(prefix, build.env.get(
                'LIBDIR', default='lib'), 'mixxx')
            build.env.Append(
                CPPDEFINES=('UNIX_LIB_PATH', r'\"%s\"' % lib_path))

    def depends(self, build):
        return [SoundTouch, ReplayGain, Ebur128Mit, PortAudio, PortMIDI, Qt, TestHeaders,
                FidLib, SndFile, FLAC, OggVorbis, OpenGL, TagLib, ProtoBuf,
                Chromaprint, RubberBand, SecurityFramework, CoreServices, IOKit,
                QtScriptByteArray, Reverb, FpClassify, PortAudioRingBuffer, LAME]

    def post_dependency_check_configure(self, build, conf):
        """Sets up additional things in the Environment that must happen
        after the Configure checks run."""
        if build.platform_is_windows:
            if build.toolchain_is_msvs:
                if not build.static_dependencies or build.build_is_debug:
                    build.env.Append(LINKFLAGS=['/nodefaultlib:LIBCMT.lib',
                                                '/nodefaultlib:LIBCMTd.lib'])

                build.env.Append(LINKFLAGS='/entry:mainCRTStartup')
                # Declare that we are using the v120_xp toolset.
                # http://blogs.msdn.com/b/vcblog/archive/2012/10/08/windows-xp-targeting-with-c-in-visual-studio-2012.aspx
                build.env.Append(CPPDEFINES='_USING_V110_SDK71_')
                # Makes the program not launch a shell first.
                # Minimum platform version 5.01 for XP x86 and 5.02 for XP x64.
                if build.machine_is_64bit:
                    build.env.Append(LINKFLAGS='/subsystem:windows,5.02')
                else:
                    build.env.Append(LINKFLAGS='/subsystem:windows,5.01')
                # Force MSVS to generate a manifest (MSVC2010)
                build.env.Append(LINKFLAGS='/manifest')
            elif build.toolchain_is_gnu:
                # Makes the program not launch a shell first
                build.env.Append(LINKFLAGS='--subsystem,windows')
                build.env.Append(LINKFLAGS='-mwindows')
