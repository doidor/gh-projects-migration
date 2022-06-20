"""
Functions that fetch data from the GitHub GraphQL API.
"""
import json

from queries import projects_data, project_issues, project_prs
from graphql.utils import run_query, ItemQueryType


def get_projects_data(
    headers, user, repository, project_old, project_new, user_type, column_mapping=None
):
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
    not_found_columns = []

    if column_mapping is not None:
        for old_column_name, new_column_name in column_mapping.items():
            old_column_id = next(
                (
                    column["id"]
                    for column in project_data_old["columns"]
                    if column["name"].lower() == old_column_name.lower()
                ),
                None,
            )

            if old_column_id is None:
                raise Exception(
                    f"Column {old_column_name} not found on project {project_old}"
                )

            new_column_id = next(
                (
                    column["id"]
                    for column in project_data_new["columns"]
                    if column["name"].lower() == new_column_name.lower()
                ),
                None,
            )

            if new_column_id is None:
                raise Exception(
                    f"Column {new_column_name} not found on project {project_new}"
                )

            column_mappings[old_column_id] = new_column_id

    else:
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
                not_found_columns.append(column["name"])
            else:
                column_mappings[column["id"]] = new_column["id"]

    ret = {
        "old": project_data_old,
        "new": project_data_new,
        "column_mappings": column_mappings,
        "new_project_status_field": new_project_status_field,
        "not_found_columns": not_found_columns,
    }

    return ret


def get_project_items(
    headers, user_type, user, repository, project, query_type=ItemQueryType.ISSUE
):
    result_query_object = (
        "issues" if query_type == ItemQueryType.ISSUE else "pullRequests"
    )

    def run_items_query(after=None):
        after_cursor = "" if after is None else f', after: "{after}"'

        query_template = (
            project_issues.query_template
            if query_type == ItemQueryType.ISSUE
            else project_prs.query_template
        )

        query = query_template.substitute(
            {
                "user_type": user_type,
                "user": user,
                "repository": repository,
                "after_cursor": after_cursor,
            }
        )

        result = run_query(query, headers)

        repo_issues = result["data"][user_type]["repository"][result_query_object][
            "edges"
        ]
        pagination_data = result["data"][user_type]["repository"][result_query_object][
            "pageInfo"
        ]

        ret = {
            result_query_object: [],
            "pagination_data": pagination_data,
        }

        for item in repo_issues:
            for project_card in item["node"]["projectCards"]["edges"]:
                if project_card["node"]["project"]["name"] == project:
                    ret[result_query_object].append(
                        {
                            "id": item["node"]["id"],
                            "title": item["node"]["title"],
                            "status": project_card["node"]["column"]["id"],
                        }
                    )

        return ret

    run = run_items_query()
    items = run[result_query_object]
    counter = 1
    print(f"Fetched page #1 (100 items / page)")

    while run["pagination_data"]["hasNextPage"]:
        run = run_items_query(run["pagination_data"]["endCursor"])
        items.extend(run[result_query_object])
        counter += 1
        print(f"Fetched page #{counter}")

    return items
