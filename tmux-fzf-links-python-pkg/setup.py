from setuptools import setup, find_packages

setup(
    name="tmux_fzf_links",
    version="1.0.0",
    author="Andrea Alberti",
    author_email="a.alberti82@gmail.com",
    description="A tool for opening links in tmux with fuzzy search",
    long_description=open("../README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/alberti42/tmux-fzf-links",
    license="MIT",
    packages=find_packages(),  # Automatically discover package modules
    include_package_data=False,  # Include non-code files from MANIFEST.in
    install_requires=[
    ],
    entry_points={
        "console_scripts": [
            "tmux_fzf_links=tmux_fzf_links.__main__:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
