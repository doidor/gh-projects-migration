from string import Template

single_item_query_raw = """
  $issue_move_name: addProjectNextItem(input: {projectId: "$project_id", contentId: "$issue_id"}) {
    projectNextItem {
      id
    }
  }
"""

query_raw = """
mutation {
  $group_issue_move
}
"""

single_item_query_template = Template(single_item_query_raw)
query_template = Template(query_raw)
