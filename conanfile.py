from conans import ConanFile, VisualStudioBuildEnvironment, tools
import os

class IcuConan(ConanFile):
    name = "icu"
    version = "59.1"
    license="http://www.unicode.org/copyright.html#License"
    description = 'ICU is a mature, widely used set of C/C++ and Java libraries providing Unicode and Globalization support for software applications.'
    url = "https://github.com/bincrafters/conan-icu"
    settings = "os", "arch", "compiler", "build_type"
    source_url = "http://download.icu-project.org/files/icu4c/{0}/icu4c-{1}-src".format(version,version.replace('.', '_'))
    options = {"with_io": [True, False]}
    default_options = "with_io=False"

    def source(self):
        if self.settings.os == 'Windows':
            tools.get("{0}.zip".format(self.source_url))
        else:
            tools.get("{0}.tgz".format(self.source_url))

    def build(self):
        root_path = self.conanfile_directory.replace('\\', '/')
        src_path = os.path.join(root_path, self.name, 'source')
        if self.settings.os == 'Windows':
            sln_file = os.path.join(src_path,"allinone","allinone.sln")
            vcvars_command = tools.vcvars_command(self.settings)
            targets = ["i18n","common","stubdata"]
            if self.options.with_io:
                targets.append('io')
            build_command = tools.build_sln_command(self.settings, sln_file, targets=targets)
            build_command = build_command.replace('"x86"','"Win32"')
            command = "{0} && {1}".format(vcvars_command, build_command)
            self.run(command)
        else:
            platform = ''
            if self.settings.os == 'Linux':
                if self.settings.compiler == 'gcc':
                    platform = 'Linux/gcc'
                else:
                    platform = 'Linux'
            elif self.settings.os == 'Macos':
                platform = 'MacOSX'
            enable_debug = ''
            if self.settings.build_type == 'Debug':
                enable_debug = '--enable-debug'
            self.run("cd {0} && bash runConfigureICU {1} {2} --prefix={3}".format(
                src_path, enable_debug, platform, os.path.join(root_path,'output')))
            self.run("cd {0} && make install".format(src_path))

    def package(self):
        if self.settings.os == 'Windows':
            libs = ['in', 'uc', 'dt']
            if self.options.with_io:
                libs.append('io')
            bin_dir = 'lib'
            lib_dir = 'lib'
            if self.settings.arch == 'x86_64':
                bin_dir = 'bin64'
                lib_dir = 'lib64'
            bin_dir = os.path.join(self.name, bin_dir)
            lib_dir = os.path.join(self.name, lib_dir)
            self.output.info("BIN_DIR = {0}".format(bin_dir))
            self.output.info("LIB_DIR = {0}".format(lib_dir))
            for lib in libs:
                self.copy(pattern="*icu{0}*.dll".format(lib), dst="lib", src=bin_dir, keep_path=False)
                self.copy(pattern="*icu{0}*.exp".format(lib), dst="lib", src=lib_dir, keep_path=False)
                self.copy(pattern="*icu{0}*.lib".format(lib), dst="lib", src=lib_dir, keep_path=False)
        else:
            install_path = "output"
            self.copy("*", "include", "{0}/include".format(install_path), keep_path=True)
            libs = ['i18n', 'uc', 'data']
            if self.options.with_io:
                libs.append('io')
            for lib in libs:
                self.copy(pattern="*icu{0}.dylib".format(lib), dst="lib", src="{0}/lib".format(install_path), keep_path=False)
                self.copy(pattern="*icu{0}.so".format(lib), dst="lib", src="{0}/lib".format(install_path), keep_path=False)

    def package_info(self):
        self.cpp_info.libs = self.collect_libs()
