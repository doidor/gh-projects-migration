from string import Template

query_raw = """
query {
  user(login: "$user") {
    repository(name: "$repository") {
      id
      name
      projects(first: 10, search: "$project_old") {
        edges {
          node {
            id
            name
            columns(first: 10) {
              edges {
                node {
                  id
                  name
                }
              }
            }
          }
        }
      }
      projectsNext(first: 1, query: "$project_new") {
        edges {
          node {
            id
            title
            fields(first: 10) {
              nodes {
                name
                id
                settings
              }
            }
          }
        }
      }
      issues(first: 100) {
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
      }
    }
  }
}
"""

query_template = Template(query_raw)
