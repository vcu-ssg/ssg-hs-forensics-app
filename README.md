# SSG - App for High School forensics exercises



## Activities

* If you want to run SAM on an image, jump into the ./reports folder and review <example1.qmd>. This file can be used as a template for running SAM in single images.

        cd reports
        quarto render example1.qmd

* If you want to rebuild the front-end:

        cd forensics-ui
        quarto render

* If you want to rebuild and run the web application:

        cd forensics-backend
        docker compose up -d
        http://localhost

* If you want to quickly set up a workstation to serve a module:

        cd workstation
        docker compose up -d
        http://localhost

## Tools to install

This system requires that the host workstation have various software tools installed and ready to run.  This suite of software tools varies, depending on what the user expects to do:

* quarto
* docker desktop
* make
* pyenv 
* poetry

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

