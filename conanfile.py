from conans import ConanFile, tools, AutoToolsBuildEnvironment
import os
import glob
import shutil


class IcuConan(ConanFile):
    name = "icu"
    version = "59.1"
    license = "http://www.unicode.org/copyright.html#License"
    description = "ICU is a mature, widely used set of C/C++ and Java libraries providing Unicode and Globalization support for software applications."
    url = "https://github.com/bincrafters/conan-icu"
    settings = "os", "arch", "compiler", "build_type"
    options = {"with_data": [True, False],
               "with_msys": [True, False],
               "shared": [True, False],
               "data_packaging": ["shared", "static", "files", "archive"]}

    default_options = "with_data=False", \
                      "with_msys=True", \
                      "shared=True", \
                      "data_packaging=archive"

    def config_options(self):
        if self.settings.os != "Windows":
            self.options.with_msys = "False"

    def build_requirements(self):
        if self.options.with_msys:
            self.build_requires("msys2_installer/latest@bincrafters/stable")
        elif self.settings.os == 'Windows' and 'MSYS_ROOT' not in os.environ:
            raise Exception("MSYS_ROOT environment variable must exist if with_msys=False.")        


    def source(self):
        icu_url =  "http://download.icu-project.org/files/icu4c"
        version_underscore = self.version.replace('.', '_')
        source_url = "{0}/{1}/icu4c-{2}-src".format(icu_url, self.version, version_underscore)
        data_url = "{0}/{1}/icu4c-{2}-data.zip".format(icu_url, self.version, version_underscore)
        
        archive_type = "tgz"
        self.output.info("Fetching sources: {0}.{1}".format(source_url, archive_type))
        tools.get("{0}.{1}".format(source_url, archive_type))

        if self.options.with_data:
            data_path = os.path.join('icu', 'source', 'data')
            self.output.info("Deleting incomplete data folder from icu sources: {0}".format(data_url))
            shutil.rmtree(data_path) 
            self.output.info("Fetching data: {0}".format(data_url))
            tools.get(data_url)                
            self.output.info("Moving data from {0} to {1}".format('data', data_path))
            os.rename('data', data_path)
        
        config_guess_url = r'http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.guess;hb=HEAD'
        self.output.info("Fetching config file: {0}.{1}".format(source_url, archive_type))
        tools.download(config_guess_url, 'config.guess')
        
        config_sub_url = r'http://git.savannah.gnu.org/gitweb/?p=config.git;a=blob_plain;f=config.sub;hb=HEAD'
        self.output.info("Fetching sources: {0}.{1}".format(source_url, archive_type))
        tools.download(config_sub_url, 'config.sub')
        if self.settings.os == 'Windows':
            # Prevent multiple CL.EXE writes to the same .PDB file (use /FS)        
            runConfigureICU_file = os.path.join(self.name,'source','runConfigureICU')
            tools.replace_in_file(runConfigureICU_file, 
            '        DEBUG_CFLAGS=\'-Zi -MDd\'\n', 
            '        DEBUG_CFLAGS=\'-Zi -MDd -FS\'\n', strict=True)
            
            tools.replace_in_file(runConfigureICU_file, 
            '        DEBUG_CXXFLAGS=\'-Zi -MDd\'\n', 
            '        DEBUG_CXXFLAGS=\'-Zi -MDd -FS\'\n', strict=True)
            
        else:
            # This allows building ICU with multiple gcc compilers (overrides fixed compiler name)
            runConfigureICU_file = os.path.join(self.name,'source','runConfigureICU')
            tools.replace_in_file(runConfigureICU_file, '        CC=gcc; export CC\n', '', strict=True)
            tools.replace_in_file(runConfigureICU_file, '        CXX=g++; export CXX\n', '', strict=True)
            
    def build(self):
        src_path = os.path.join(self.build_folder, 'icu', 'source')
        data_path = os.path.join(src_path, 'data')
        output_path = os.path.join(self.build_folder, 'output')
        build_path = os.path.join(self.build_folder, 'icu', 'build')
        
        os.mkdir(build_path)
            
        if self.options.with_data:
            tools.replace_in_file(
                os.path.join(data_path, 'makedata.mak'),
                r'GODATA "$(ICU_LIB_TARGET)" "$(TESTDATAOUT)\testdata.dat"',
                r'GODATA "$(ICU_LIB_TARGET)"')

        src_config_guess = os.path.join(self.build_folder, 'config.guess')
        dst_config_guess = os.path.join(src_path, 'config.guess')
        self.output.info("Copying from {0} to {1}".format(src_config_guess, dst_config_guess))
        shutil.copy(src_config_guess, dst_config_guess)

        src_config_sub = os.path.join(self.build_folder, 'config.sub')
        dst_config_sub = os.path.join(src_path, 'config.sub')
        self.output.info("Copying from {0} to {1}".format(src_config_sub, dst_config_sub))
        shutil.copy(src_config_sub, dst_config_sub)
                        
        arch = '64' if self.settings.arch == 'x86_64' else '32'
        enable_debug = '--enable-debug --disable-release' if self.settings.build_type == 'Debug' else ''
        enable_static = '--enable-static --disable-shared' if not self.options.shared else '--enable-shared --disable-static'
        data_packaging = '--with-data-packaging={0}'.format(self.options.data_packaging)
        
        if self.settings.os == 'Windows':
            vcvars_command = tools.vcvars_command(self.settings)
            platform = 'MSYS/MSVC'
            bash = "%MSYS_ROOT%\\usr\\bin\\bash"
            runtime = self.settings.compiler.runtime

            with tools.chdir(src_path):
                configfile = "runConfigureICU"
                if self.settings.build_type == 'Release':
                    tools.replace_in_file(configfile, "-MD", "-%s" % runtime)
                if self.settings.build_type == 'Debug':
                    tools.replace_in_file(configfile, "-MDd", "-%s -FS" % runtime)
                
                self.run(("{vcvars_command} && {bash} -c ^'./{configfile}"
                    " {enable_debug} {platform} --host=i686-pc-mingw{arch} --build=i686-pc-mingw{arch} --with-library-bits={arch}"
                    " --prefix={output_path} {enable_static} {data_packaging} --disable-layout --disable-layoutex^'").format(
                        vcvars_command=vcvars_command, 
                        bash=bash,
                        configfile=configfile,
                        enable_debug=enable_debug, 
                        platform=platform, 
                        arch=arch, 
                        output_path=tools.unix_path(output_path),
                        enable_static=enable_static, 
                        data_packaging=data_packaging))

                # There is a fragment in Makefile.in:22 of ICU that prevents from building with MSYS:
                #
                # ifneq (@platform_make_fragment_name@,mh-cygwin-msvc)
                # SUBDIRS += escapesrc
                # endif
                #
                # We patch the respective Makefile.in, to disable building it for MSYS
                #
                escapesrc_patch = os.path.join('tools', 'Makefile.in')
                tools.replace_in_file(escapesrc_patch, 'SUBDIRS += escapesrc',
                    '\tifneq (@platform_make_fragment_name@,mh-msys-msvc)\n\t\tSUBDIRS += escapesrc\n\tendif')

                env_build = AutoToolsBuildEnvironment(self)
                with tools.environment_append(env_build.vars):
                    self.run("{vcvars_command} && {bash} -c 'pacman -S make --noconfirm'".format(
                        vcvars_command=vcvars_command, 
                        bash=bash))
                        
                    self.run(("{vcvars_command} && {bash} -c ^'make --silent -j {cpu_count}").format(
                        vcvars_command=vcvars_command, 
                        bash=bash,
                        cpu_count=tools.cpu_count()))
                    
                    self.run("{vcvars_command} && {bash} -c ^'make install'".format(
                        vcvars_command=vcvars_command, 
                        bash=bash))

        else:
            env_build = AutoToolsBuildEnvironment(self)
            with tools.environment_append(env_build.vars):
                platform = ''
                if self.settings.os == 'Linux':
                    if self.settings.compiler == 'gcc':
                        platform = 'Linux/gcc'
                    else:
                        platform = 'Linux'
                elif self.settings.os == 'Macos':
                    platform = 'MacOSX'
                
                with tools.chdir(build_path):
                    self.run(("bash ../source/runConfigureICU {enable_debug} {platform} "
                        "--with-library-bits={arch} --prefix={output_path} {enable_static} {data_packaging} "
                        "--disable-layout --disable-layoutex").format(
                            enable_debug=enable_debug, 
                            platform=platform, 
                            arch=arch, 
                            output_path=output_path, 
                            enable_static=enable_static, 
                            data_packaging=data_packaging))
                            
                    self.run("make --silent -j {cpu_count} install".format(
                        cpu_count=tools.cpu_count()))

                if self.settings.os == 'Macos':
                    with tools.chdir('output/lib'):
                        for dylib in glob.glob('*icu*.{0}.dylib'.format(self.version)):
                            self.run('install_name_tool -id {0} {1}'.format(os.path.basename(dylib), dylib))

    def package(self):
        if self.settings.os == 'Windows':
            bin_dir, include_dir, lib_dir, share_dir = (os.path.join('output', path) for path in
                                                        ('bin', 'include', 'lib', 'share'))
            self.output.info('bin_dir = {0}'.format(bin_dir))
            self.output.info('include_dir = {0}'.format(include_dir))
            self.output.info('lib_dir = {0}'.format(lib_dir))
            self.output.info('share_dir = {0}'.format(share_dir))

            # we copy everything for a full ICU package
            self.copy("*", dst="bin", src=bin_dir, keep_path=True, symlinks=True)
            self.copy("*", dst="include", src=include_dir, keep_path=True, symlinks=True)
            self.copy("*", dst="lib", src=lib_dir, keep_path=True, symlinks=True)
            self.copy("*", dst="share", src=share_dir, keep_path=True, symlinks=True)

        else:
            bin_dir, include_dir, lib_dir, share_dir = (os.path.join('output', path) for path in
                                                        ('bin', 'include', 'lib', 'share'))
            self.output.info('bin_dir = {0}'.format(bin_dir))
            self.output.info('include_dir = {0}'.format(include_dir))
            self.output.info('lib_dir = {0}'.format(lib_dir))
            self.output.info('share_dir = {0}'.format(share_dir))

            # we copy everything for a full ICU package
            self.copy("*", dst="bin", src=bin_dir, keep_path=True, symlinks=True)
            self.copy("*", dst="include", src=include_dir, keep_path=True, symlinks=True)
            self.copy("*", dst="lib", src=lib_dir, keep_path=True, symlinks=True)
            self.copy("*", dst="share", src=share_dir, keep_path=True, symlinks=True)

    def package_info(self):
        self.cpp_info.libs = []
        vtag = self.version.split('.')[0]
        keep = False
        for lib in tools.collect_libs(self):
            if not vtag in lib:
                self.output.info("OUTPUT LIBRARY: " + lib)
                if lib != 'icudata':
                    self.cpp_info.libs.append(lib)
                else:
                    keep = True

        # if icudata is not last, it fails to build (is that true?)
        if keep:
            self.cpp_info.libs.append('icudata')

        self.env_info.path.append(os.path.join(self.package_folder, "lib"))
        
        if not self.options.shared:
            self.cpp_info.defines.append("U_STATIC_IMPLEMENTATION")

            if self.settings.os == 'Linux':
                self.cpp_info.libs.append('dl')

    def package_id(self):
        self.info.options.with_msys = "any" 
