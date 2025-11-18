# Proposal

This project aims to update an existing project so that we might use it in the department. It'd be a nice project for you aswell since it pertains to documentation which, boring as that is, is necessary both from a learning point of view and a future reference (when two years down the line you wonder how did you solve a given problem).

`SphinxDoc` provides the means of hosting ones Python documentation, written with Pythons' documentation system `Sphinx`, within a website, written with the `Django` web framework. `Sphinx` utilizes ReStructured Text (`RST`) which is more complete then MarkDown (`MD`) , which is provides a thin presentation shim, in that it supports multiple compilation targets e.g. PDF/Word etc. provides better cross referencing/linking including across documents and supports extention e.g. `https://mermaid.js.org/`, mathjax and so on.

The `SphinxDoc` package has been around for some time and is quite solid but the author has done little to keep it current. It does support searching within ones documentation and there is some contorl over the privacy/publicity of a given doucment.

To use it one installs it into a Django website as an application. Once installed it becomes necessary to pull down the documentation of ones projects of interest, configure each one in the web interface and compile it through the Django management command so that the package may then display it. 

It would be handy if the package were more current and improved upon the following:

 * Eased the pulling in of new projects (Given an appropriate link it should pull down the given repository)
 * Eased configuration (Once pulled down the user should be able to specify the location of the Sphinx source and configuration file)
 * Permit editing (Prior to editing the latest source should be retrieved once editing is complete the source should be committed)
 * Permit versioning of the documentation (Utilizing the tags of a git repo compile specific versions of the documentation)
 * Permit comparison (Given two different tags permit the comparison of the two revisions perhaps highlighting changes)

# Setup

This roughly outlines the setup for this project as I done it in the hopes this might be helpful to you.

## Compiler
 
In general I'd recommend installing the python compiler as normal but taking care to do the following :

    - Uncheck the box that says "Add python to the system path" and use virtual environments exclusively for each prject (See the *creates|activates|deactivates the virtual environment* lines below)
    - Version your installations as this allows different versions of the python compiler on the same machine. Some projects are heavily version specific (`C:\program files\python\VERSION\` instead of `C:\program files\python\`)

## Structure

One always needs a space for their code projects and the packages that they mean to extend:

 * Create a space for code (I usually create a partition for this so `D:\` or `C:\code\` ) and seperate my packages/projects in that space by language, framework, company and/or purpose hence `C:\code\django\sphinxdoc` and `C:\code\projects\documentation`

### Package

The package source gets pulled into the language/framework space so from the command line (win-key + R) 

   - `mkdir C:\code\django` Creates the space for "Django projects"
   - `pushd C:\code\django` Enters the space
   - `git clone git@github.com:Carelvd/django-sphinxdoc.git sphinxdoc` Clones the package
   - `pushd sphinxdoc` Enters the package root
   - `git switch version_control` Switches to the working branch
   - `popd` Exits the package root
   - `popd` Exits the "Django projects" space

### Project

The project source gets placed into the company/personal projects folder :

   - `mkdir C:\code\projects\documentation` Creates the space for projects
   - `pushd C:\code\projects\documentation` Enters the space
   - `C:\program files\python\VERSION\python.exe -m venv .env` *creates the virtual environment* a copy of the specified version of the python compiler
   - `.env\scripts\activate` *activates the virtual environment* making the compiler available for execution
   - `pip install django` installs the initial dependency; in this case the Django web framework
   - `django-admin startproject website` Creates a Django based web project (Django tends to double nest this e.g. `website\website`)
   - `move website/* .` Unwraps the folder hierarchy one layer (`website/website` -> `website`)
   - `.env\scripts\deactivate` *deactivates the virtual environment* making the compiler available for execution
   - `popd` Exits the project root
 
 ### Linking

 You may or may not have noticed at this point that the package structure is wrapped for release on the Python Package Index (PyPI) which is a bit of a cumbersome structure to work with when in development so I'd create a symbolic link from the package source (`src\sphinxdoc` under `C:\code\django\sphinxdoc`) to the project folder (`C:\code\projects\documentation`) as a django application (`C:\code\django\sphinxdoc\src\sphinxdoc` <- `C:\code\projects\documentation\sphinxdoc`).

   - `mklink /J C:\code\projects\documentation\sphinxdoc C:\code\django\sphinxdoc\src\sphinxdoc` links the sphinxdoc package into the website folder as a package

## Website

### Configuration

We need to configure the project to use the linked `sphinxdoc` application. This in turn utilizes `haystack` which wraps the selected search engine; the easiest of which to configure is `whoosh`. To do so open the `website\settings.py` file under `C:\code\projects\documentation` and modify the `INSTALLED_APPS` setting:

```
INSTALLED_APPS = [
   ...,
   'sphinxdoc',
   'haystack',
]
```

and configure Haystack to use the Whoosh engine, within the same file :

```
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': BASE_DIR/'whoosh',
    },
}
```

Django will also need to know how to navigate to the application, edit `website\urls.py` under `C:\code\projects\documentation` :

```
URL_PATTERNS = [
   ...
   path('docs/', include('sphinxdoc.urls')),
]
```


Finally install the necessary dependencies, in this case `haystack` :

   - `pushd C:\code\projects\documentation` Enters the space
   - `.env\scripts\activate` *activates the virtual environment* making the compiler available for execution
   - `pip install haystack` installs the additional dependency.
   - `.env\scripts\deactivate` *deactivates the virtual environment* making the compiler available for execution
   - `popd` Exits the project root

### Migration

Django requires a database to operate against. The structure of the database is specified through the models defined under each application configured within a given website which are mapped to the tables in the database through migrations. 

Finally install the dependencies, in this case `haystack` :

   - `pushd C:\code\projects\documentation` Enters the space
   - `.env\scripts\activate` *activates the virtual environment* making the compiler available for execution
   - `python manage.py migrate` Performs the initial migration, creating the database to which Django will connect during operation.
   - `.env\scripts\deactivate` *deactivates the virtual environment* making the compiler available for execution
   - `popd` Exits the project root

Note: If you see any error messages at this point I might've overlooked some installation/configuration step.

### Preparation

Django requires an administrator to access the site once it is up:

   - `pushd C:\code\projects\documentation` Enters the space
   - `.env\scripts\activate` *activates the virtual environment* making the compiler available for execution
   - `python manage.py createsuperuser` Creates the primary website user
   - `.env\scripts\deactivate` *deactivates the virtual environment* making the compiler available for execution
   - `popd` Exits the project root

### Operation

Django provides a development server for development purposes:

   - `pushd C:\code\projects\documentation` Enters the space
   - `.env\scripts\activate` *activates the virtual environment* making the compiler available for execution
   - `python manage.py runserver` Executes the development server that will ultimately run the project
   - `.env\scripts\deactivate` *deactivates the virtual environment* making the compiler available for execution
   - `popd` Exits the project root

This is usually accessible at `http://localhost:8000/`

## Documentation

To actually add a documentation project to be hosted through the website you will need to install sphinx :

   - `pushd C:\code\projects\documentation` Enters the space
   - `.env\scripts\activate` *activates the virtual environment* making the compiler available for execution
   - `pip install sphinx` 
   - `.env\scripts\deactivate` *deactivates the virtual environment* making the compiler available for execution
   - `popd` Exits the project root

and create a documentation project 

   - `pushd C:\code\projects\documentation` Enters the space
   - `.env\scripts\activate` *activates the virtual environment* making the compiler available for execution
   - `sphinx-quickstart PROJECT`  Replacing `PROJECT` with a better title
   - `.env\scripts\deactivate` *deactivates the virtual environment* making the compiler available for execution
   - `popd` Exits the project root

This must then be registered with the Sphinxodc extention (So start the websote as above, navigate to `http://localhost:8000//admin`) and add the project under sphinxdoc.

   - `pushd C:\code\projects\documentation` Enters the space
   - `.env\scripts\activate` *activates the virtual environment* making the compiler available for execution
   - `python manage.py updatedoc` Build the various documentation projects
   - `.env\scripts\deactivate` *deactivates the virtual environment* making the compiler available for execution
   - `popd` Exits the project root

Note: If there is an error here one should consult the sphinxdoc documentation `https://django-sphinxdoc.readthedocs.io/en/latest/quickstart.html`
