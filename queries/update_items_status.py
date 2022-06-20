from string import Template

single_item_query_raw = """
    $item_update_name: updateProjectNextItemField(
        input: {projectId: "$project_id", itemId: "$item_id", value: "$new_status_id", fieldId: "$status_field_id"}
    ) {
        clientMutationId
    }
"""

query_raw = """
mutation {
  $group_items_update
}
"""

single_item_query_template = Template(single_item_query_raw)
query_template = Template(query_raw)
