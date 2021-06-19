function changeTheme(v) {
    if (v.checked) {
        Style.setDark();
    } else {
        Style.setLight();
    }
}

window.onload = function () {
    const v = $("#darkModeSwitch");
    v.prop('checked', Style.getTheme() !== "light");
}

function changeNameVisibility(v) {
    const set_visible = v.checked;
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/set_name_visible');
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onerror = function () {
        console.log(xhr.responseText);
        v.checked = !set_visible;
    };
    xhr.send(JSON.stringify({
        visible: set_visible,
    }));
}

function deleteAccount() {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/remove_user');
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function () {
        window.location.replace("/logout");
    };
    xhr.onerror = function () {
        console.log(xhr.responseText);
    };
    xhr.send(JSON.stringify({}));
}
