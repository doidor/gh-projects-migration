from string import Template

single_item_query_raw = """
  $item_move_name: addProjectNextItem(input: {projectId: "$project_id", contentId: "$item_id"}) {
    projectNextItem {
      id
    }
  }
"""

query_raw = """
mutation {
  $group_items_move
}
"""

single_item_query_template = Template(single_item_query_raw)
query_template = Template(query_raw)
