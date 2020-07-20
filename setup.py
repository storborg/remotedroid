from setuptools import setup, find_packages


setup(
    name="remotedroid",
    version="0.0.1.dev",
    description="Webapp to remotely control Android devices via adb",
    long_description="",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="android adb vnc remote viewer",
    url="https://github.com/storborg/remotedroid",
    author="Scott Torborg",
    author_email="storborg@gmail.com",
    install_requires=["starlette", "aiofiles", "jinja2", "uvicorn",],
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points="""\
      [console_scripts]
      remotedroid = remotedroid.cmd:main
      """,
)
