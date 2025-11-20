# SSG - App for High School forensics exercises

In Fall 2025 the Software for Social Good (SSG) team partners with the Forensics lab at VCU to review their SAM model pipeline.

SAM (Segment Anything Model) is an open-source foundation model for image segmentation released by Meta AI. It’s designed to produce high-quality segmentation masks for any object in any image, even for objects it has never seen during training.

The SSG team converted their jupyter scripts to Quarto QMD files.

Further, the SSG team developed a larger, workstation based webapp and server for use by High School students visiting the Forensics Lab.  The SSG team
created a model lab Lesson, setting the foundation for future lesson developments.

This repo contains all the source code and images used by the SSG team.  This repo can be used by different personas:

* The lab manager - wanting to install the software in preparation for a tour of the Forensics lab,
* A research student - wanting to run SAM on an image,
* A research student - wanting to create and deploy a new lesson for system,
* A developer - wanting a full install to extend the system.

Additional documentation can be found on [this project's ghpages site](https://vcu-ssg.github.io/ssg-hs-forensics-app).

## Prerequisites

There are some key pieces of software to installed, regardless of how you plan to use this repo.  We make extensive use of the command line terminal (powershell on windows).  Press the ⊞ key and enter "Terminal" to start it up. 

* [docker desktop](https://docs.docker.com/desktop/setup/install/windows-install/) - Because of security, etc. this needs to be installed manually.  It requires admin priveleges and is installed system-wide on your machine.

* Scoop windows package manager.  This tool can be used to install all the other software.

        # Install scoop package manager for windows
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
        Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

* Once scoop is installed, here are some useful snippets that can be pasted to the command line:

        # Install core scoop buckets
        scoop bucket add main
        scoop bucket add extras
        scoop bucket add versions

        # Install help unix tools
        scoop install make
        scoop install busybox
        scoop install git
        scoop install gh

* If you plan to edit and build QMD, lessons or other files locally:

        scoop install vscode-portable
        scoop install quarto

* If you plan to run SAM locally, you'll need to install more tools.

        # Remove pre-installed python.  This really screws things up
        Remove-Item "$env:LOCALAPPDATA\Microsoft\WindowsApps\python*.exe"
        Get-AppxPackage *python* | Remove-AppxPackage

        # Next, install pyenv
        Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"

        # You'll need to close the terminal and re-open it at this point.  
        # You might get "<file not found>" or other errors if you don't.

        # Install python necessary for SAM
        pyenv update
        pyenv install 3.11.9
        pyenv global 3.11.9

        # Install poetry
        (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

        # check everything
        pyenv --version
        python --version
        poetry --version


That's it!  You should be able to undertake any of the major activities below.

## Major Activities

Many of the activities below have been automated in the Makefile found in the project home directory.  To see the automated commands, open a terminal, move the project repo home and enter:

        make
        
Here is an example of what gets displayed:

        Available commands:
        -------------------
        help    Show this help message
        forensics-ui    Build the frontend using Quarto
        forensics-backend       Build the backend without running server
        start-server    Start backend in detached mode (listens on localhost:80)
        stop-server     Stop backend server
        open-webapp     Start server (if needed) and open the browser

Any of the commands can be run directly from the command line, for example:

        make start-server

Here are the explicit commands from the command line.  These are intended as reminders, your mileage may very.

* If you want to run SAM on an image, jump into the ./reports folder and review [reports/example1.qmd](./reports/example1.qmd). This file can be used as a template for running SAM in single images.  Here is the [report created by quarto](https://vcu-ssg.github.io/ssg-hs-forensics-app/example1.html)..

        cd reports
        make download-sam
        quarto render example1.qmd

* If you want to rebuild the front-end:

        cd forensics-ui
        quarto render

* If you want to rebuild and run the web application, first rebuild the front-end, then:

        cd forensics-backend
        docker compose up -d
        http://localhost

* If you want to quickly set up a workstation to serve a module:

        cd workstation
        docker compose up -d
        http://localhost


* If you want to install the necessary tools on WINDOWS we HIGHLY recommend using scoop:

        # Install scoop package manager for windows
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
        Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

        # Install core scoop buckets
        scoop bucket add main
        scoop bucket add extras
        scoop bucket add versions

        # Core tools
        scoop install vscode-portable
        scoop install quarto
        scoop install make
        scoop install pyenv
        scoop install poetry

        # Unix tools
        scoop install busybox


## Tools to install

This system requires that the host workstation have various software tools installed and ready to run.  This suite of software tools varies, depending on what the user expects to do:

* [Visual studio code](https://code.visualstudio.com/download) - for editing files,
* [Quarto](https://quarto.org/docs/get-started/) - for rendering qmd files into HTML,
* [Docker desktop](https://docs.docker.com/desktop/setup/install/windows-install/) - for building and hosting the webapp.
* make - tool for automating activities
* pyenv - python version selection tool
* poetry - python library and virtual environment manager

The system can be built under Windows (powershell), Linux (wsl/ubuntu), or Mac (zsh). 

## FOLDERS

* ./forensics-ui : this folder contains the source for our Workstation webapp.  The webapp is writting using Quarto and javascript.  When rendered, site website is stored inside the ./forensics-ui/_site folder and is used by the back-end to present the application.

* ./forensics-backend : this folder contains the backend, middleware and webserver application.  The backend was written using python and docker and leverages fastapi and nginx.

* ./sample-images : this is where a bunch of sample images are stored.  These are the source images, edited or processed images should not be stored in this folder.

* ./sample-code : contains the sample python and collab/jupyter files provided by Alina.

* ./reports : this is where our initial quarto reports/qmd files should be stored.  The file contains the source files for the website, too.

* ./reports/index.qmd : this is the source code for the *index.html* ghpages website home page.

* ./docs : do not edit files in this folder.  This folder is created automatically by quarto or other tools and is used by GH-PAGES for presentation of project website.

* ./src : source code for any app(s) that we create.

