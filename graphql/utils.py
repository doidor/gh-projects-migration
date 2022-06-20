import requests

from enum import Enum


class ItemQueryType(Enum):
    ISSUE = 0
    PR = 1


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
        print(request)
        raise Exception(
            f"Query failed to run by returning code of {request.status_code}, with the message {request.text}. {query}"
        )
