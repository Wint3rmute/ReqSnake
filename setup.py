from setuptools import setup

setup(
    name='mkdocs-reqsnake',
    version='0.1.0',
    packages=["mkdocs_reqsnake"],
    install_requires=[
        'mkdocs>=1.6',
        'mkdocs-material>=9.6'
    ],
    entry_points={
        'mkdocs.plugins': [
            'reqsnake = mkdocs_reqsnake.plugin:ReqSnake'
        ]
    }
)
