from setuptools import setup, find_packages

def take_package_name(name):
    if name.startswith("-e"):
        return name[name.find("=")+1:name.rfind("-")]
    else:
        return name.strip()

def load_requires_from_file(filepath):
    with open(filepath) as fp:
        return [take_package_name(pkg_name) for pkg_name in fp.readlines()]

def load_links_from_file(filepath):
    res = []
    with open(filepath) as fp:
        for pkg_name in fp.readlines():
            if pkg_name.startswith("-e"):
                res.append(pkg_name.split(" ")[1])
    return res

# long_description = read_file("README.rst")
# version = read_file("VERSION")
version = "0.1.0"

setup(
    name = 'ofpeditor',
    version = version,
    author = 'Kazunari Kaizu',
    author_email = 'kwaizu@gmail.com',
    url = 'https://github.com/kaizu/protocol_editor',
    description = 'The OFP editor',
    # long_description_content_type = "text/x-rst",  # If this causes a warning, upgrade your setuptools package
    # long_description = long_description,
    license = "MIT license",
    packages = find_packages(exclude=["nodes", "hotkeys"]),  # Don't include test directory in binary distribution
    install_requires=load_requires_from_file("requirements.txt"),
    dependency_links=load_links_from_file("requirements.txt"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]  # Update these accordingly
)