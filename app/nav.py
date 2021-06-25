from typing import Optional

from cuwais.config import config_file
from cuwais.database import User


def make_nav_item(text, icon=None, link='#', data_toggle=None):
    return dict(text=text,
                icon=icon if icon is not None else "",
                link=link,
                data_toggle=data_toggle)


def make_nav_item_from_name(name):
    link = f'/{name}'
    return make_nav_item(text=name.capitalize(), link=link)


def make_l_nav(user: Optional[User]):
    places = []
    if user is not None:
        places += ['leaderboard', 'submissions']
    places += ['about']

    items = [make_nav_item_from_name(name) for name in places]
    return items


def make_r_nav(user: Optional[User]):
    items = []
    if user is None:
        items.append(
            make_nav_item(text='Log In', icon='fa fa-sign-in', link='#loginModal', data_toggle='modal'))
    else:
        if user.is_admin:
            items.append(make_nav_item_from_name("admin"))
        items.append(
            make_nav_item(text="You", link='/me'))
        items.append(
            make_nav_item(text='Log Out', icon='fa fa-sign-out', link='javascript:login.logout();'))
    return items


def get_nav(user):
    return dict(
        soc_name=config_file.get("soc_name").upper(),
        l_nav=make_l_nav(user),
        r_nav=make_r_nav(user)
    )
