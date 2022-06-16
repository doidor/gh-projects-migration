# How to migrate old GitHub projects to GitHub Projects (Beta)?

This tool is inspired by [this project migration tutorial](https://github.com/pl-strflt/projects-migration), but modified to use Python for the sake of simplicity and better code organization.

## Prerequisites

Please make sure to check out [the original repository prerequisites](https://github.com/pl-strflt/projects-migration#prerequisites) for this tool to work, especially the [GitHub token](https://github.com/pl-strflt/projects-migration#github-token) and [New Project](https://github.com/pl-strflt/projects-migration#new-project) paragraphs

## Column names mapping

The script supports a config file (in json format) that can parse the `column_mapping` field. This means that you can assign different names to new project columns and just map them in the config file, **case insensitive**. Something like:

```json
# config.json
{
  [..]
  "column_mapping": {
    "to do": "planned"
  }
}
```

If this option is specified, the script **will migrate only issues in these columns**, otherwise you will need to do exact name matching for all columns (ie the new project would have to have the same columns as the old one).

You can also point multiple columns to a single one. Example:

```json
# config.json
{
  [..]
  "column_mapping": {
    "to do": "planned",
    "later": "planned",
    [..]
  }
}

```

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
