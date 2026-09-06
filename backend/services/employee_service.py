from backend.repositories.employee_repo import get_all_employees, add_employee, delete_employee_by_login, update_last_online

def load_employees():
    rows = get_all_employees()

    return [
        {
            "id": row.get("id"),
            "username": row.get("username"),
            "role": row.get("role"),
            "last_online": row.get("last_online")
        }
        for row in rows
    ]


def remove_employee_by_login(username):
    return delete_employee_by_login(username)


def update_employee_last_online(username):
    return update_last_online(username)