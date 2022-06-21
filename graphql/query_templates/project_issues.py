from string import Template

query_raw = """
query {
  $user_type(login: "$user") {
    repository(name: "$repository") {
      id
      name
      issues(first: 100, filterBy: {states: OPEN} $after_cursor) {
        edges {
          node {
            id
            projectCards(first: 10) {
              edges {
                node {
                  id
                  project {
                    id
                    name
                  }
                  column {
                    id
                    name
                  }
                }
              }
            }
            closed
            title
            state
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
}
"""

query_template = Template(query_raw)
