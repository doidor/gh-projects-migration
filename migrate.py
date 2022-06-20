import argparse
import json
import sys

from github import Github

from graphql.queries import get_project_items, get_projects_data
from graphql.mutations import do_copy_items, do_update_items
from graphql.utils import ItemQueryType

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrate issues from an old Github project to a Beta one."
    )

    parser.add_argument(
        "--dry-run",
        default=False,
        action="store_true",
        help="Only get data without any updates",
    )

    parser.add_argument("--token", default=None, help="Github user token")

    parser.add_argument("--user", default=None, help="Github user")
    parser.add_argument("--repository", default=None, help="Github repository")
    parser.add_argument("--project_old", default=None, help="Old github project name")
    parser.add_argument("--project_new", default=None, help="New github project name")

    parser.add_argument("--config", default=None, help="Config file path")

    args = parser.parse_args()
    dry_run = args.dry_run

    user = None
    repository = None
    project_old = None
    project_new = None
    token = None
    column_mapping = None

    if args.config is not None:
        try:
            config_file = open(args.config)
            config_data = json.load(config_file)

            user = config_data["user"]
            repository = config_data["repository"]
            project_old = config_data["project_old"]
            project_new = config_data["project_new"]
            token = config_data["token"]
            column_mapping = None

            if "column_mapping" in config_data:
                column_mapping = config_data["column_mapping"]

        except Exception as e:
            print(f"Error opening config file: {e}")
            sys.exit(1)
    else:
        user = args.user
        repository = args.repository
        project_old = args.project_old
        project_new = args.project_new
        token = args.token

    if (
        token is None
        or user is None
        or repository is None
        or project_old is None
        or project_new is None
    ):
        raise Exception(
            "You can either provide a config file, or a token, user, repository, project_old and project_new"
        )

    headers = {"Authorization": f"Bearer {token}"}
    github_rest = Github(token)
    is_org = github_rest.get_user(user).type.lower() == "organization" or False
    user_type = "organization" if is_org else "user"

    data = get_projects_data(
        headers,
        user,
        repository,
        project_old,
        project_new,
        user_type,
        column_mapping,
    )

    print("Fetching issues...")
    issues = get_project_items(headers, user_type, user, repository, project_old)

    print("Fetching PRs...")
    prs = get_project_items(
        headers,
        user_type,
        user,
        repository,
        project_old,
        ItemQueryType.PR,
    )

    print("Gathered projects data.")

    if dry_run:
        print("Dry run, no updates will be made.")
        print(json.dumps(data, indent=2))
        print(json.dumps(issues, indent=2))
        print(json.dumps(prs, indent=2))

        sys.exit(0)

    if len(data["not_found_columns"]) > 0:
        raise Exception(
            f"Not found columns in the new project: {data['not_found_columns']}. Please make sure to manually create the columns."
        )

    issues = [issue for issue in issues if issue["status"] in data["column_mappings"]]

    move_issues_ret = do_copy_items(headers, data["new"]["id"], issues)
    print("Copied issues.")

    move_prs_ret = do_copy_items(headers, data["new"]["id"], prs)
    print("Copied PRs.")

    new_issues_status = []
    new_prs_status = []

    for pr_old, pr_new in move_issues_ret.items():
        pr_status = next(
            (
                data["column_mappings"][issue["status"]]
                for issue in issues
                if issue["id"] == pr_old
            ),
            None,
        )

        new_issues_status.append({"id": pr_new, "status": pr_status})

    update_ret = do_update_items(
        headers,
        data["new"]["id"],
        new_issues_status,
        data["new_project_status_field"]["id"],
    )

    print("Updated issues.")

    for pr_old, pr_new in move_prs_ret.items():
        pr_status = next(
            (data["column_mappings"][pr["status"]] for pr in prs if pr["id"] == pr_old),
            None,
        )

        new_prs_status.append({"id": pr_new, "status": pr_status})

    update_ret = do_update_items(
        headers,
        data["new"]["id"],
        new_prs_status,
        data["new_project_status_field"]["id"],
    )

    print("Updated PRs.")
