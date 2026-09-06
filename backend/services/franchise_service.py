from backend.repositories.franchise_repo import get_all_franchises, add_franchise


def load_franchises():
    rows = get_all_franchises()

    return [
        {
            "contract_id": row.get("contract_id"),
            "contact_person": row.get("contact_person"),
            "organization": row.get("organization"),
            "phone": row.get("phone"),
            "email": row.get("email"),
            "address": row.get("address"),
            "start_date": row.get("start_date"),
            "end_date": row.get("end_date"),
            "status": row.get("status"),
            "royalty_percentage": row.get("royalty_percentage"),
            "initial_fee": row.get("initial_fee"),
            "monthly_fee": row.get("monthly_fee")
        }
        for row in rows
    ]


def create_new_franchise(contact_person, organization, phone, email, address,
                         start_date, end_date, status, royalty_percentage,
                         initial_fee, monthly_fee):
    return add_franchise(contact_person, organization, phone, email, address,
                         start_date, end_date, status, royalty_percentage,
                         initial_fee, monthly_fee)