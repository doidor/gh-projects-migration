from string import Template

query_raw = """
query {
  $user_type(login: "$user") {
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
      projectsNext(first: 10, query: "$project_new") {
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
    }
  }
}
"""

query_template = Template(query_raw)
