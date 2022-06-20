from queries import move_items, update_items_status
from graphql.utils import run_query


def do_copy_items(headers, project_id, items):
    """
    Move items from the old project to the new one.
    """
    mutation_prefix = "MoveItem_"
    move_items_query = [
        move_items.single_item_query_template.substitute(
            {
                "project_id": project_id,
                "item_id": item["id"],
                "item_move_name": f"{mutation_prefix}{counter}",
            }
        )
        for (counter, item) in enumerate(items, 1)
    ]
    move_items_query = "".join(move_items_query)

    query = move_items.query_template.substitute(
        {
            "group_items_move": move_items_query,
        }
    )

    result = run_query(query, headers)

    result = result["data"]
    items_id_mapping = {
        items[i]["id"]: result[item]["projectNextItem"]["id"]
        for (i, item) in enumerate(result)
    }

    return items_id_mapping


def do_update_items(headers, project_id, items, status_field_id):
    """
    Update items status on the new board to match the old one.
    """
    mutation_prefix = "UpdateItem_"
    update_items_query = [
        update_items_status.single_item_query_template.substitute(
            {
                "project_id": project_id,
                "item_id": item["id"],
                "new_status_id": item["status"],
                "status_field_id": status_field_id,
                "item_update_name": f"{mutation_prefix}{counter}",
            }
        )
        for (counter, item) in enumerate(items, 1)
    ]
    update_items_query = "".join(update_items_query)

    query = update_items_status.query_template.substitute(
        {
            "group_items_update": update_items_query,
        }
    )

    result = run_query(query, headers)
    return result
