import argparse
import json
import requests
import sys

from queries import move_issues, projects_data, update_issues_status, project_issues
from github import Github


def run_query(query, headers):
    """
    Runs a Github GraphQL query and returns the result.
    """
    request = requests.post(
        "https://api.github.com/graphql", json={"query": query}, headers=headers
    )
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(
            "Query failed to run by returning code of {}. {}".format(
                request.status_code, query
            )
        )


def get_projects_data(headers, user, repository, project_old, project_new, user_type):
    """
    Fetches new and old projects data.
    """

    query = projects_data.query_template.substitute(
        {
            "user_type": user_type,
            "user": user,
            "repository": repository,
            "project_old": project_old,
            "project_new": project_new,
        }
    )

    result = run_query(query, headers)
    result_data = result["data"][user_type]["repository"]
    result_data_old = result_data["projects"]["edges"]

    if len(result_data_old) == 0:
        raise Exception(f"Project {project_old} not found")

    result_data_old = result_data_old[0]["node"]

    if result_data_old is None:
        raise Exception(f"Project {project_old} not found")

    project_data_old = {
        "id": result_data_old["id"],
        "name": result_data_old["name"],
        "columns": [
            {"id": column["node"]["id"], "name": column["node"]["name"]}
            for column in result_data_old["columns"]["edges"]
        ],
    }

    result_data_new = [
        project
        for project in result_data["projectsNext"]["edges"]
        if project["node"]["title"] == project_new
    ]

    if len(result_data_new) == 0:
        raise Exception(f"Project {project_new} not found")

    result_data_new = result_data_new[0]["node"] or None

    if result_data_new is None:
        raise Exception(f"Project {project_new} not found")

    new_project_status_field = [
        field
        for field in result_data_new["fields"]["nodes"]
        if field["name"] == "Status"
    ][0] or None

    if new_project_status_field is None:
        raise Exception(f"Status field not found on project {project_new}")

    new_project_columns = json.loads(new_project_status_field["settings"])["options"]
    project_data_new = {
        "id": result_data_new["id"],
        "name": result_data_new["title"],
        "columns": new_project_columns,
    }

    column_mappings = {}

    for column in project_data_old["columns"]:
        new_column = next(
            (
                new_col
                for new_col in project_data_new["columns"]
                if new_col["name"].lower() == column["name"].lower()
            ),
            None,
        )

        if new_column is None:
            raise Exception(
                f"Column {column['name']} not found in new project. Please make sure to manually clone all the columns from the old project to the new one."
            )

        column_mappings[column["id"]] = new_column["id"]

    ret = {
        "old": project_data_old,
        "new": project_data_new,
        "column_mappings": column_mappings,
        "new_project_status_field": new_project_status_field,
    }

    return ret


def get_project_issues(headers, user_type, user, repository, project):
    def run_issues_query(after=None):
        after_cursor = "" if after is None else f', after: "{after}"'

        query = project_issues.query_template.substitute(
            {
                "user_type": user_type,
                "user": user,
                "repository": repository,
                "after_cursor": after_cursor,
            }
        )

        result = run_query(query, headers)

        repo_issues = result["data"][user_type]["repository"]["issues"]["edges"]
        pagination_data = result["data"][user_type]["repository"]["issues"]["pageInfo"]

        ret = {
            "issues": [],
            "pagination_data": pagination_data,
        }

        for issue in repo_issues:
            for project_card in issue["node"]["projectCards"]["edges"]:
                if project_card["node"]["project"]["name"] == project:
                    ret["issues"].append(
                        {
                            "id": issue["node"]["id"],
                            "title": issue["node"]["title"],
                            "status": project_card["node"]["column"]["id"],
                        }
                    )

        return ret

    run = run_issues_query()
    issues = run["issues"]
    counter = 1
    print(f"Fetched page #1 (100 issues / page)")

    while run["pagination_data"]["hasNextPage"]:
        run = run_issues_query(run["pagination_data"]["endCursor"])
        issues.extend(run["issues"])
        counter += 1
        print(f"Fetched page #{counter}")

    return issues


def do_copy_issues(headers, project_id, issues):
    """
    Move issues from the old project to the new one.
    """
    mutation_prefix = "MoveIssue_"
    move_issues_query = [
        move_issues.single_item_query_template.substitute(
            {
                "project_id": project_id,
                "issue_id": issue["id"],
                "issue_move_name": f"{mutation_prefix}{counter}",
            }
        )
        for (counter, issue) in enumerate(issues, 1)
    ]
    move_issues_query = "".join(move_issues_query)

    query = move_issues.query_template.substitute(
        {
            "group_issue_move": move_issues_query,
        }
    )

    result = run_query(query, headers)

    result = result["data"]
    issues_id_mapping = {
        issues[i]["id"]: result[issue]["projectNextItem"]["id"]
        for (i, issue) in enumerate(result)
    }

    return issues_id_mapping


def do_update_issues(headers, project_id, issues, status_field_id):
    """
    Update issues status on the new board to match the old one.
    """
    mutation_prefix = "UpdateIssue_"
    update_issues_query = [
        update_issues_status.single_item_query_template.substitute(
            {
                "project_id": project_id,
                "issue_id": issue["id"],
                "new_status_id": issue["status"],
                "status_field_id": status_field_id,
                "issue_update_name": f"{mutation_prefix}{counter}",
            }
        )
        for (counter, issue) in enumerate(issues, 1)
    ]
    update_issues_query = "".join(update_issues_query)

    query = update_issues_status.query_template.substitute(
        {
            "group_issues_update": update_issues_query,
        }
    )

    result = run_query(query, headers)
    return result


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

    required_named = parser.add_argument_group("required named arguments")

    required_named.add_argument(
        "--token", default=None, help="Github user token", required=True
    )
    required_named.add_argument(
        "--user", default=None, help="Github user", required=True
    )
    required_named.add_argument(
        "--repository", default=None, help="Github repository", required=True
    )
    required_named.add_argument(
        "--project_old", default=None, help="Old github project name", required=True
    )
    required_named.add_argument(
        "--project_new", default=None, help="New github project name", required=True
    )

    args = parser.parse_args()
    dry_run = args.dry_run

    headers = {"Authorization": f"Bearer {args.token}"}
    github_rest = Github(args.token)
    is_org = github_rest.get_user(args.user).type.lower() == "organization" or False
    user_type = "organization" if is_org else "user"

    try:
        projects_data = get_projects_data(
            headers,
            args.user,
            args.repository,
            args.project_old,
            args.project_new,
            user_type,
        )

        issues = get_project_issues(
            headers, user_type, args.user, args.repository, args.project_old
        )
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

    print("Gathered projects data.")

    if dry_run:
        print("Dry run, no updates will be made.")
        print(json.dumps(projects_data, indent=2))
        print(json.dumps(issues, indent=2))

        sys.exit(0)

    move_issues_ret = do_copy_issues(headers, projects_data["new"]["id"], issues)
    print("Copied issues.")

    new_issues_status = []

    for issue_old, issue_new in move_issues_ret.items():
        issue_status = next(
            (
                projects_data["column_mappings"][issue["status"]]
                for issue in issues
                if issue["id"] == issue_old
            ),
            None,
        )

        new_issues_status.append({"id": issue_new, "status": issue_status})

    update_ret = do_update_issues(
        headers,
        projects_data["new"]["id"],
        new_issues_status,
        projects_data["new_project_status_field"]["id"],
    )
    print("Updated issues.")
