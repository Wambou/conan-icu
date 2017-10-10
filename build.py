from conan.packager import ConanMultiPackager, os, sys, re
import platform

from collections import defaultdict

if __name__ == "__main__":

    reponame_a = os.getenv("APPVEYOR_REPO_NAME","")
    repobranch_a = os.getenv("APPVEYOR_REPO_BRANCH","")

    reponame_t = os.getenv("TRAVIS_REPO_SLUG","")
    repobranch_t = os.getenv("TRAVIS_BRANCH","")

    if reponame_t or reponame_a:
        username, repo = reponame_a.split("/") if reponame_a else reponame_t.split("/")
        channel, version = repobranch_a.split("/") if repobranch_a else repobranch_t.split("/")
        
        with open("conanfile.py", "r") as conanfile:
            contents = conanfile.read()
            name = re.search(r'name\s*=\s*"(\S*)"', contents).groups()[0]
            version = re.search(r'version\s*=\s*"(\S*)"', contents).groups()[0]
        
        os.environ["CONAN_USERNAME"] = username
        os.environ["CONAN_CHANNEL"] = channel
        os.environ["CONAN_REFERENCE"] = "{0}/{1}".format(name, version)
        os.environ["CONAN_UPLOAD"]="https://api.bintray.com/conan/{0}/public-conan".format(username)
        os.environ["CONAN_REMOTES"]="https://api.bintray.com/conan/{0}/public-conan".format(username)
    
    builder = ConanMultiPackager()
    
    if platform.system() == "Windows":
        current_settings={
            "arch":os.environ["CONAN_ARCHS"], 
            "compiler.version": os.environ["CONAN_VISUAL_VERSIONS"], 
            "compiler.runtime": os.environ["CONAN_VISUAL_RUNTIMES"]}

        builder.add(settings=current_settings, options={"icu:shared": True, "icu:with_data": True})
        builder.add(settings=current_settings, options={"icu:shared": True, "icu:with_data": False})
        builder.add(settings=current_settings, options={"icu:shared": False, "icu:with_data": True})
        builder.add(settings=current_settings, options={"icu:shared": False, "icu:with_data": False})
    else:
        current_settings={"arch":os.environ["CONAN_ARCHS"]}
        builder.add(settings=current_settings, options={"icu:shared": True, "icu:with_data": True})
        builder.add(settings=current_settings, options={"icu:shared": True, "icu:with_data": False})
        builder.add(settings=current_settings, options={"icu:shared": False, "icu:with_data": True})
        builder.add(settings=current_settings, options={"icu:shared": False, "icu:with_data": False})
    
    builder.run()
