from typing import Optional

from cuwais.database import User

from server import data


def make_nav_item(text, icon=None, active=False, link='#', data_toggle=None):
    return dict(text=text, icon=icon, active=active, link=link, data_toggle=data_toggle)


def make_nav_item_from_name(name, current_dir):
    is_active = (name == current_dir)
    link = f'/{name}' if not is_active else '#'
    return make_nav_item(text=name.capitalize(), link=link, active=is_active)


def make_l_nav(user: Optional[User], current_dir):
    places = []
    if user is not None:
        places += ['leaderboard', 'submissions']
    places += ['about']

    items = [make_nav_item_from_name(name, current_dir) for name in places]
    return items


def make_r_nav(user: Optional[User], current_dir):
    items = []
    if user is None:
        items.append(
            make_nav_item(text='Log In', icon='fa fa-sign-in', link='#loginModal', data_toggle='modal'))
    else:
        if user.is_admin:
            items.append(make_nav_item_from_name("admin", current_dir))
        items.append(
            make_nav_item(text="You", link='/me' if current_dir != 'me' else '#',
                          active=(current_dir == 'me')))
        items.append(
            make_nav_item(text='Log Out', icon='fa fa-sign-out', link='/logout'))
    return items


def extract_session_objs(user, current_dir):
    return dict(
        user=user,
        l_nav=make_l_nav(user, current_dir),
        r_nav=make_r_nav(user, current_dir)
    )
