# How to migrate old GitHub projects to GitHub Projects (Beta)?

This tool is inspired by [this project migration tutorial](https://github.com/pl-strflt/projects-migration), but modified to use Python for the sake of simplicity and better code organization.

## Prerequisites

Please make sure to check out [the original repository prerequisites](https://github.com/pl-strflt/projects-migration#prerequisites) for this tool to work, especially the [GitHub token](https://github.com/pl-strflt/projects-migration#github-token) and [New Project](https://github.com/pl-strflt/projects-migration#new-project) paragraphs

## Usage

The tool usage is pretty straight forward:

1. `pip install -r requirements.txt`
1. Follow the tool help guide:

```
usage: migrate.py [-h] [--dry-run] --token TOKEN --user USER --repository REPOSITORY --project_old
                  PROJECT_OLD --project_new PROJECT_NEW

Migrate issues from an old Github project to a Beta one.

options:
  -h, --help            show this help message and exit
  --dry-run             Only get data without any updates

required named arguments:
  --token TOKEN         Github user token
  --user USER           Github user
  --repository REPOSITORY
                        Github repository
  --project_old PROJECT_OLD
                        Old github project name
  --project_new PROJECT_NEW
                        New github project name
```
