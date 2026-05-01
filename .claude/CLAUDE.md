# CLAUDE.md

## Project Overview
- This project is a webserver for hosting a static site
- It includes tools for deploying the webserver and site content to a local machine (for testing) or a remote server
- Logging and log rotation functionality is included. 
- A section for admin pages is provided for extension capabilities.

## Project Tooling
- The webserver is written in Python/Flask

## Deployment
- Deploy remote: `./deploy.py server`
- Deploy locally: `./deploy.py local`
- Deploy remote site contents: `./deploy.py server-site <zip_file>`
- Deploy local site contents: `./deploy.py server-site <zip_file>`

## Directory Structure
- `deploy.py` is the deployment tool
- `backups/` contains zip files of site content
- `server/` contains the webserver code
- `resources/` contains assets used by the webserver code such as images, css, and js
- `admin_pages/` contains jinja templates used for management pages (not the static site content)
  
## Behavior Guidelines
- Don’t assume. Don’t hide confusion. Surface tradeoffs.
- Minimum code that solves the problem. Nothing speculative.
- Touch only what you must. Clean up only your own mess.
- Define success criteria. Loop until verified.