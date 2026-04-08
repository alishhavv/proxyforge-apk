from setuptools import setup, find_packages

setup(
    name='proxyforge',  # Replace with the package name
    version='0.1.0',  # Replace with the package version
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'proxyforge=proxyforge.main:main',  # Replace with your main module and function
        ],
    },
    install_requires=[
        'requests',  # Add required dependencies here
        'flask',    
        'other_dependency',  # Add more dependencies as needed
    ],
    description='A standalone application for proxy forging',  # Package description
    author='alishhavv',  # Your name or organization
    author_email='youremail@example.com',  # Replace with your email
    url='https://github.com/alishhavv/proxyforge-apk',  # Project URL
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',  # Specify your Python version requirement
)
