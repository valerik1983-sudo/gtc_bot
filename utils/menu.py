from database import get_user
from database import get_referrals_count

from keyboards import get_main_menu

from database import is_admin


def get_user_main_menu(user_id):

    user = get_user(user_id)

    team_count = get_referrals_count(
        user_id
    )

    return get_main_menu(
        registered=user is not None,
        has_team=team_count > 0,
        is_admin=is_admin(user_id)
    )