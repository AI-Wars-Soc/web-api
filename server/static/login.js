function onGoogleSignIn(googleUser) {
    const id_token = googleUser.getAuthResponse().id_token;
    const error_message = $("#login-error-msg");

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/login_google');
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function () {
        if (xhr.status >= 300) {
            console.log("Could not sign in");
            error_message.show();
            return;
        }
        error_message.hide();
        console.log('Signed in as: ' + xhr.responseText);
        window.location.replace("/home");
    };
    xhr.onerror = function () {
        console.log("Could not sign in");
        error_message.show();
    };
    xhr.send(JSON.stringify({
        idtoken: id_token
    }));
}